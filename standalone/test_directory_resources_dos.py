#!/usr/bin/env python3
"""Exercise real DOS8086 canonical lookup, strict resources and retained claims."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
NAMES=['blank-resets-defaults','local-directory-pair','PCPLUS-environment-pair',
 'named-META-default-fallback','missing-directory-resets-defaults','CLI-provenance-profile6',
 'missing-explicit-CLI','invalid-binding-even-under-CLI','unsupported-profile',
 'invalid-keyboard-slot','invalid-actions-after-keyboard','close-error-already-closed',
 'close-error-still-open','capture-keyboard-conflict','monitor-actions-conflict',
 'existing-dynamic-reservation','release-error','CWD-drift-after-first-open',
 'canonical-error','metadata-error','readonly-resources','missing-profile-block',
 'actions-suffix-rejected','invalid-PCPLUS-environment','second-selection-resets-bindings',
 'second-selection-failure-preserves-old-bundle','invalid-default-keyboard',
 'unbound-relative-CLI-path','canonical-over63','resource-is-directory',
 'second-content-open-failure','first-content-open-failure',
 'fixed-recorder-keyboard-conflict','fixed-recorder-actions-conflict',
 'snapshot-keyboard-conflict','history-actions-conflict']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def keyboard(tag,blocks=7):
 return b''.join((f'{tag}{profile}{slot:02}'.encode()+b'\0'+bytes([0x80+slot%64])*7)[:12]
  for profile in range(blocks) for slot in range(79))
def actions(tag):
 return b''.join(struct.pack('<H',i%4)+(f'{tag}{i}'.encode()+b'\0'+bytes([0xc0+i])*52)[:52] for i in range(10))
DEFAULTS=b''.join(bytes([ord('A')+i%26])+bytes(11) for i in range(79))
DISABLED=b''.join(b'\3'+bytes(53) for _ in range(10))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 build=ROOT/'build/directory-resources';manifest=json.loads((build/'manifest.json').read_text())
 assert not manifest['original_inputs'] and sha(build/'RESOURCE.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);shutil.copyfile(build/'RESOURCE.EXE',out/'RESOURCE.EXE')
 (out/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/resource_noinherit.asm'),'-o',str(out/'NOINH.COM')],check=True)
 (out/'ENV').mkdir();(out/'OTHER').mkdir()
 (out/'ENV/BOARD.KBD').write_bytes(keyboard('E'));(out/'ENV/BOARD.KEY').write_bytes(actions('E'))
 (out/'OTHER/BOARD.KBD').write_bytes(keyboard('D'));(out/'OTHER/BOARD.KEY').write_bytes(actions('D'))
 commands=[];originals={}
 for mode in range(len(NAMES)):
  case=out/f'T{mode:03}';case.mkdir()
  if mode not in (2,3,4,23):
   kbd=keyboard('L',4 if mode==21 else 7)
   if mode==9:kbd=kbd[:4*948]+b'BAD-SLOT-XXX!'+kbd[4*948+12:]
   (case/'BOARD.KBD').write_bytes(kbd)
   key=bytearray(actions('L'))
   if mode==10:struct.pack_into('<H',key,0,4)
   (case/'BOARD.KEY').write_bytes(key+(b'X' if mode==22 else b''))
  if mode==3:(case/'PCPLUS.KBD').write_bytes(keyboard('F'))
  if mode in (5,6,7):
   (case/'CLI.KBD').write_bytes(keyboard('C'));(case/'CLI.KEY').write_bytes(actions('C'))
  originals.update({str(f.relative_to(out)):f.read_bytes() for f in case.iterdir()})
  commands += [f'cd \\T{mode:03}',f'set PCPLUS={"C:\\ENV" if mode==2 else "C:\\BAD;ENV" if mode==23 else ""}']
  if mode==20:commands+=['attrib +r BOARD.KBD','attrib +r BOARD.KEY']
  commands += [f'..\\RESOURCE {mode} >RESULT.TXT','if errorlevel 1 goto failed']
 commands += ['cd \\','echo PASS>PASS.TXT','goto capture',':failed','cd \\','echo FAIL>FAIL.TXT',':capture','SNAP A','exit']
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
'''+ '\n'.join(commands)+'\n'
 (out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=180)
 assert run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(p.parent.name,p.read_text()) for p in out.glob('T*/RESULT.TXT')]
 assert len((out/'BEFORE.BIN').read_bytes())==42 and (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes()
 for n,data in originals.items():assert (out/n).read_bytes()==data,n
 reports=[]
 for mode,name in enumerate(NAMES):
  case=out/f'T{mode:03}';fields=struct.unpack('<9H',(case/'RESULT.BIN').read_bytes())
  assert fields[0]==mode and not fields[8]
  data=(case/'BUNDLE.BIN').read_bytes();assert len(data)==1624
  state=(case/'STATE.BIN').read_bytes();assert len(state)==142
  if fields[1]:assert data==b'\xcc'*1624
  else:
   expected=bytearray(1624);profile=6 if mode==5 else 4
   source=(0,0) if mode in (0,4,24) else (3,0) if mode==3 else (1,1) if mode==5 else (2,2)
   mask=0 if source==(0,0) else 512 if mode==3 else 4608
   struct.pack_into('<4H',expected,0,profile,mask,*source)
   tag='E' if mode==2 else 'F' if mode==3 else 'C' if mode==5 else 'L'
   if mask&512:
    path='C:\\ENV\\BOARD.KBD' if mode==2 else f'C:\\T{mode:03}\\'+('PCPLUS.KBD' if mode==3 else 'CLI.KBD' if mode==5 else 'BOARD.KBD')
    expected[8:8+len(path)+1]=path.encode()+b'\0'
   if mask&4096:
    path='C:\\ENV\\BOARD.KEY' if mode==2 else f'C:\\T{mode:03}\\'+('CLI.KEY' if mode==5 else 'BOARD.KEY')
    expected[72:72+len(path)+1]=path.encode()+b'\0'
   expected[136:1084]=keyboard(tag)[profile*948:(profile+1)*948] if mask&512 else DEFAULTS
   expected[1084:]=actions(tag) if mask&4096 else DISABLED
   assert data==expected,(name,next((i for i,(a,b) in enumerate(zip(data,expected)) if a!=b),None))
  phase,status,source,dos,close,claim,release=struct.unpack_from('<7H',state)
  if fields[7]:assert phase==3
  if mode==24:assert phase==2 and status==0
  reports.append(dict(case=name,mode=mode,status=fields[1],assertions=fields[2],content_opens=fields[3],content_closes=fields[4],canonical_calls=fields[5],metadata_calls=fields[6],held=bool(fields[7])))
 assert (out/'OTHER/BOARD.KBD').read_bytes()==keyboard('D') and (out/'OTHER/BOARD.KEY').read_bytes()==actions('D')
 report=dict(passed=True,case_count=len(reports),native_assertions=sum(r['assertions'] for r in reports),cases=reports,
  binary_sha256=manifest['binary_sha256'],sources=manifest['sources'],original_inputs=[],hardware_restored=True,
  exact_success_bundles=True,failed_bundles_unchanged=True,resource_files_unchanged=True,
  noninheritable_child_witness=True,
  test_sources={n:sha(ROOT/n) for n in ['standalone/test_directory_resources_dos.py','standalone/test_terminal.py','standalone/resource_noinherit.asm']},
  limitations=manifest['limitations'],artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(reports),'DOS8086 workflows /',report['native_assertions'],'assertions')
if __name__=='__main__':main()
