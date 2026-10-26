#!/usr/bin/env python3
"""Actual startup adapter -> frozen CLI provenance -> selected resource bytes."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from test_terminal import SAMPLER
from test_directory_resources_dos import keyboard,actions
ROOT=Path(__file__).resolve().parents[1]
NAMES=['directory-derived-flags-are-not-CLI','both-relative-CLI-resources','keyboard-only-CLI',
 'actions-only-CLI','bound-CLI-survives-CWD-drift','directory-lookup-uses-current-CWD',
 'lowercase-absolute-CLI-normalized','first-canonical-error','second-canonical-error',
 'overlong-canonical-identity','invalid-keyboard-path','invalid-actions-path',
 'rebind-refused-original-identities-retained','missing-CLI-file-no-implicit-fallback',
 'invalid-CLI-actions-after-keyboard-read','raw-selected-record-retained','CLI-profile6']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 build=ROOT/'build/directory-resource-cli';manifest=json.loads((build/'manifest.json').read_text())
 assert not manifest['original_inputs'] and sha(build/'CLI.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);shutil.copyfile(build/'CLI.EXE',out/'CLI.EXE')
 (out/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 (out/'OTHER').mkdir();(out/'OTHER/BOARD.KBD').write_bytes(keyboard('D'));(out/'OTHER/BOARD.KEY').write_bytes(actions('D'))
 commands=[];originals={}
 for mode in range(len(NAMES)):
  case=out/f'T{mode:03}';case.mkdir()
  (case/'BOARD.KBD').write_bytes(keyboard('L'));(case/'BOARD.KEY').write_bytes(actions('L'))
  if mode!=13:(case/'CLI.KBD').write_bytes(keyboard('C'))
  key=bytearray(actions('C'))
  if mode==14:struct.pack_into('<H',key,0,4)
  (case/'CLI.KEY').write_bytes(key)
  originals.update({str(f.relative_to(out)):f.read_bytes() for f in case.iterdir()})
  commands += [f'cd \\T{mode:03}','set PCPLUS=',f'..\\CLI {mode} >RESULT.TXT','if errorlevel 1 goto failed']
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
 with (out/'dosbox.log').open('w') as log:run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=180)
 assert run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(p.parent.name,p.read_text()) for p in out.glob('T*/RESULT.TXT')]
 assert len((out/'BEFORE.BIN').read_bytes())==42 and (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes()
 for n,data in originals.items():assert (out/n).read_bytes()==data,n
 reports=[]
 for mode,name in enumerate(NAMES):
  case=out/f'T{mode:03}';fields=struct.unpack('<7H',(case/'RESULT.BIN').read_bytes());assert fields[0]==mode
  cli=(case/'CLI.BIN').read_bytes();request=(case/'REQUEST.BIN').read_bytes();bundle=(case/'BUNDLE.BIN').read_bytes()
  assert len(cli)==138 and len(request)==248 and len(bundle)==1624
  if 7<=mode<=11:
   assert struct.unpack_from('<H',cli)[0]==3 and request==b'\xa5'*248 and bundle==b'\xcc'*1624
   assert cli[10:]==bytes(128)
  else:
   mask=fields[5]&4608;profile=6 if mode==16 else 4
   kbpath=f'C:\\T{mode:03}\\CLI.KBD' if mask&512 else ''
   keypath=f'C:\\T{mode:03}\\CLI.KEY' if mask&4096 else ''
   expected_cli=struct.pack('<5H',2,fields[5],0,0,0)+kbpath.encode().ljust(64,b'\0')+keypath.encode().ljust(64,b'\0')
   assert cli==expected_cli,name
   record=bytearray(114);record[0x56:0x56+6]=b'BOARD\0';record[0x5f:0x5f+6]=b'BOARD\0'
   if mode==15:
    record[:0x56]=bytes((i*37+0x80)&255 for i in range(0x56));record[0x68:]=bytes((i*17+3)&255 for i in range(0x68,114))
   assert request[:114]==record and struct.unpack_from('<HH',request,114)==(profile,mask)
   assert struct.unpack_from('<H',request,118)[0]!=0 and request[120:]==expected_cli[10:]
   if mode in (13,14):assert bundle==b'\xcc'*1624
   else:
    kbsource=1 if mask&512 else 2;keysource=1 if mask&4096 else 2
    prefix='C:\\OTHER' if mode==5 else f'C:\\T{mode:03}'
    if not kbpath:kbpath=prefix+'\\BOARD.KBD'
    if not keypath:keypath=prefix+'\\BOARD.KEY'
    expected=struct.pack('<4H',profile,4608,kbsource,keysource)+kbpath.encode().ljust(64,b'\0')+keypath.encode().ljust(64,b'\0')
    kbtag='C' if mask&512 else 'D' if mode==5 else 'L';keytag='C' if mask&4096 else 'D' if mode==5 else 'L'
    expected+=keyboard(kbtag)[profile*948:(profile+1)*948]+actions(keytag)
    assert bundle==expected,name
  reports.append(dict(case=name,mode=mode,assertions=fields[1],bind_status=fields[2],resource_status=fields[3],canonical_calls=fields[4],original_mask=fields[5],CLI_state=fields[6]))
 result=dict(passed=True,case_count=len(reports),native_assertions=sum(r['assertions'] for r in reports),cases=reports,
  binary_sha256=manifest['binary_sha256'],sources=manifest['sources'],original_inputs=[],hardware_restored=True,source_resources_unchanged=True,
  test_sources={n:sha(ROOT/n) for n in ['standalone/test_directory_resource_cli_dos.py','standalone/test_directory_resources_dos.py','standalone/test_terminal.py']},
  limitations=manifest['limitations'],artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'DOS8086 CLI/resource workflows /',result['native_assertions'],'assertions')
if __name__=='__main__':main()
