#!/usr/bin/env python3
"""Real DOS8086 resource claims, close ambiguity, rollback and noninheritance."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from test_directory_resources_dos import keyboard,actions
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES=['all-resources','XLT-close-still-open','XLT-close-already-closed','fixed-claim-conflict','XLT-open-error','XLT-read-error','release-error','CWD-drift-after-first-open','relative-CLI-refused','invalid-mode-before-CLI-override','request-output-alias','canonical-error','metadata-error','failed-second-stage-preserves-first','mode0-no-XLT-read','mode2-no-XLT-read']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 built=ROOT/'build/directory-translation';m=json.loads((built/'manifest.json').read_text());assert not m['original_inputs'] and sha(built/'TRANSLAT.EXE')==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 shutil.copyfile(built/'TRANSLAT.EXE',out/'TRANSLAT.EXE')
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/resource_noinherit.asm'),'-o',str(out/'NOINH.COM')],check=True)
 (out/'OTHER').mkdir();(out/'OTHER/BOARD.KBD').write_bytes(keyboard('D'));(out/'OTHER/BOARD.KEY').write_bytes(actions('D'));(out/'OTHER/PCPLUS.XLT').write_bytes(bytes(256))
 commands=[];originals={}
 for mode in range(len(NAMES)):
  case=out/f'T{mode:03}';case.mkdir();(case/'BOARD.KBD').write_bytes(keyboard('N'));(case/'BOARD.KEY').write_bytes(actions('N'));(case/'PCPLUS.XLT').write_bytes(bytes((i*73+19)%256 for i in range(256)))
  originals.update({str(f.relative_to(out)):f.read_bytes() for f in case.iterdir()})
  commands += [f'cd \\T{mode:03}',f'..\\TRANSLAT {mode} >RESULT.TXT','if errorlevel 1 goto failed']
 commands+=['cd \\','echo PASS>PASS.TXT','exit',':failed','cd \\','echo FAIL>FAIL.TXT','exit']
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nset PCPLUS=\n'+'\n'.join(commands)+'\n'
 (out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=100)
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(n,(out/f'T{i:03}/RESULT.TXT').read_text()) for i,n in enumerate(NAMES) if (out/f'T{i:03}/RESULT.TXT').exists()]
 reports=[]
 for i,name in enumerate(NAMES):
  case=out/f'T{i:03}';mode,checks,opens,closes,reads,held,bad,status=struct.unpack('<8H',(case/'RESULT.BIN').read_bytes());assert mode==i and checks>0 and not bad
  bundle=(case/'BUNDLE.BIN').read_bytes();assert len(bundle)==1948
  if status:assert bundle==b'\xcc'*1948
  else:
   expected=bytes((j*73+19)%256 for j in range(256)) if i not in (14,15) else bytes(256)
   assert bundle[1692:]==expected
   assert struct.unpack_from('<H',bundle,1624)[0]==(0 if i==14 else 2 if i==15 else 1)
  reports.append(dict(case=name,passed=True,native_assertions=checks,content_opens=opens,closes=closes,XLT_reads=reads,held=bool(held),status=status))
 for n,b in originals.items():assert (out/n).read_bytes()==b,n
 result=dict(passed=True,binary_sha256=m['binary_sha256'],cases=reports,case_count=len(reports),native_assertions=sum(c['native_assertions'] for c in reports),noninheritable_child_witness=True,original_inputs=[],
  sources=m['sources'],test_sources={n:sha(ROOT/n) for n in ['standalone/test_directory_translation_dos.py','standalone/test_directory_resources_dos.py','standalone/resource_noinherit.asm']},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Component uses real DOS IO; declared open/read/close/release/canonical/metadata faults are adapters, not physical errors. Application handoff has separate native tests.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'DOS workflows,',result['native_assertions'],'native assertions')
if __name__=='__main__':main()
