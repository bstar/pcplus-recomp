#!/usr/bin/env python3
"""Actual DOS32-length script fingerprints, ASX/ASP lookup and retained claims."""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,zlib
from pathlib import Path
from test_directory_resources_dos import keyboard,actions
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES=['blank-script','compiled','compiled-over64KiB','header128','bad-header-no-ASP-fallback','empty-compiled','fragmented-reads','current-ASP','PCPLUS-ASP','PCPLUS-ASX-before-current-ASP','qualified-script','missing-script','empty-source-needs-compiler','script-open-error','script-read-error','script-close-still-open','script-close-already-closed','fixed-script-claim','release-error','CWD-drift','bad-stored-name','malformed-environment-current-ASP','oversized-read-count','failed-second-stage-preserves-first','absolute-script','space-blank-script','directory-ASX-no-ASP-fallback','script-metadata-error']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 built=ROOT/'build/directory-scripts';m=json.loads((built/'manifest.json').read_text());assert not m['original_inputs'] and sha(built/'SCRIPTS.EXE')==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 shutil.copyfile(built/'SCRIPTS.EXE',out/'SCRIPTS.EXE');subprocess.run(['nasm','-fbin',str(ROOT/'standalone/resource_noinherit.asm'),'-o',str(out/'NOINH.COM')],check=True)
 valid=compile_source('proc main\nfopen 0 "RAN" "wb"\nfputs 0 "UNEXPECTED"\nfclose 0\nendproc\n');source=b'proc main\nendproc\n'
 large=bytes([128])+bytes(range(256))*384
 (out/'GO.ASX').write_bytes(valid)
 (out/'OTHER').mkdir();(out/'OTHER/GO.ASX').write_bytes(b'\x80DECOY');(out/'OTHER/BOARD.KBD').write_bytes(keyboard('D'));(out/'OTHER/BOARD.KEY').write_bytes(actions('D'));(out/'OTHER/PCPLUS.XLT').write_bytes(bytes(256))
 commands=[];originals={};selected={}
 for mode in range(len(NAMES)):
  case=out/f'T{mode:03}';case.mkdir();env=out/f'E{mode:03}';env.mkdir()
  (case/'BOARD.KBD').write_bytes(keyboard('N'));(case/'BOARD.KEY').write_bytes(actions('N'));(case/'PCPLUS.XLT').write_bytes(bytes(range(256)))
  target=case/'GO.ASX';kind=1;data=valid
  if mode==2:data=large
  if mode==3:data=b'\x80'
  if mode==4:data=b'\x81INVALID';(case/'GO.ASP').write_bytes(source)
  if mode==5:data=b''
  if mode in (7,12,21):target=case/'GO.ASP';kind=2;data=b'' if mode==12 else source
  if mode==8:target=env/'GO.ASP';kind=2;data=source
  if mode==9:target=env/'GO.ASX';(case/'GO.ASP').write_bytes(source)
  if mode==10:(case/'A').mkdir();target=case/'A/GO.ASX'
  if mode==24:target=out/'GO.ASX'
  if mode==26:target.mkdir();(case/'GO.ASP').write_bytes(source)
  elif mode not in (0,11,20,25):target.write_bytes(data)
  if mode not in (0,11,20,25,26):selected[mode]=(target,kind,data)
  env_value=r'C:\BAD;ENV' if mode==21 else f'C:\\E{mode:03}'
  commands += [f'cd \\T{mode:03}',f'set PCPLUS={env_value}',f'..\\SCRIPTS {mode} >RESULT.TXT','if errorlevel 1 goto failed']
 originals={str(f.relative_to(out)):f.read_bytes() for f in out.rglob('*') if f.is_file() and f.suffix in ('.KBD','.KEY','.XLT','.ASX','.ASP')}
 commands+=['cd \\','echo PASS>PASS.TXT','exit',':failed','cd \\','echo FAIL>FAIL.TXT','exit']
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\n'+'\n'.join(commands)+'\n';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=150)
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(n,(out/f'T{i:03}/RESULT.TXT').read_text()) for i,n in enumerate(NAMES) if (out/f'T{i:03}/RESULT.TXT').exists()]
 reports=[]
 for i,name in enumerate(NAMES):
  case=out/f'T{i:03}';mode,checks,opens,closes,reads,held,bad,status,detail=struct.unpack('<9H',(case/'RESULT.BIN').read_bytes());assert mode==i and checks>0 and not bad
  bundle=(case/'BUNDLE.BIN').read_bytes();assert len(bundle)==2024
  if status:assert bundle==b'\xcc'*2024
  else:
   if i in (0,25):expected=bytes(76)
   else:
    path,kind,data=selected[i];identity='C:\\'+str(path.relative_to(out)).replace('/',chr(92))
    expected=identity.encode().ljust(64,b'\0')+struct.pack('<HHII',kind,data[0] if kind==1 else 0,len(data),zlib.crc32(data))
   assert bundle[1948:]==expected,(name,bundle[1948:],expected)
  reports.append(dict(case=name,passed=True,native_assertions=checks,content_opens=opens,closes=closes,script_reads=reads,held=bool(held),status=status,detail=detail))
 for n,data in originals.items():assert (out/n).read_bytes()==data,n
 assert not list(out.rglob('RAN')),'Script preflight must not execute a script'
 result=dict(passed=True,binary_sha256=m['binary_sha256'],cases=reports,case_count=len(reports),native_assertions=sum(c['native_assertions'] for c in reports),CRC_oracle='Python zlib.crc32 over whole selected file including header',largest_script_bytes=len(large),noninheritable_child_witness=True,original_inputs=[],sources=m['sources'],test_sources={n:sha(ROOT/n) for n in ['standalone/test_directory_scripts_dos.py','standalone/test_directory_resources_dos.py','standalone/test_terminal.py','standalone/resource_noinherit.asm','src/aspect/compiler.py']},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Explicit diagnostic faults; no actual script is executed by preflight. Source candidates still require compilation; header checking is not complete bytecode validation.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'script DOS workflows,',result['native_assertions'],'assertions')
if __name__=='__main__':main()
