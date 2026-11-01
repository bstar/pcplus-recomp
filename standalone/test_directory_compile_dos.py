#!/usr/bin/env python3
"""DOS compiler-owner claims, real ASPCOMP, and explicit fault-child recovery."""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES=['real-compiler','syntax-error','source-changed-before-EXEC','existing-target','missing-helper','source-owner-conflict','target-owner-conflict','helper-owner-conflict','scratch-owner-conflict','release-uncertainty','source-close-uncertainty','fault-child-changes-source','fault-child-no-output','fault-child-fails-with-output','fault-child-bad-header','63-byte-source-path','far-alias-and-dirty-owner','target-is-directory','long-canonical-scratch-conflict']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 built=ROOT/'build/directory-compile';m=json.loads((built/'manifest.json').read_text());cm=json.loads((ROOT/'build/aspect-compiler-dos/manifest.json').read_text())
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 for n,h in cm['sources'].items():assert sha(ROOT/n)==h,n
 assert sha(built/'DCOMPILE.EXE')==m['binary_sha256'] and sha(built/'FAULT.EXE')==m['fault_child_sha256']
 assert sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')==cm['binary_sha256']
 for src,dst in [(built/'DCOMPILE.EXE','DCOMPILE.EXE'),(built/'FAULT.EXE','FAULT.EXE'),(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE','REAL.EXE')]:shutil.copyfile(src,out/dst)
 source=b'proc main\nfopen 0 "RAN" "wb"\nfputs 0 "UNEXPECTED"\nfclose 0\nendproc\n';expected=compile_source(source.decode())
 commands=[];cases=[]
 for i in range(len(NAMES)):
  case=out/f'T{i:03}'
  if i in (15,18):
   for part in ['ABCDEFGH','IJKLMNOP','QRSTUVWX','YZABCDEF','GHIJKLMN','ABC']:case/=part
  case.mkdir(parents=True);cases.append(case);(case/'GO.ASP').write_bytes(b'proc main\nBAD BAD BAD\nendproc\n' if i==1 else source)
  cwd='C:\\'+str(case.relative_to(out)).replace('/',chr(92))
  if i in (15,18):assert len(cwd+'\\GO.ASP')==63
  commands+=['cd \\','del ASPCOMP.EXE >NUL']
  if i!=4:commands+=['copy '+('FAULT.EXE' if i in (11,12,13,14) else 'REAL.EXE')+' ASPCOMP.EXE >NUL']
  commands+=['set LOCFAULT='+str(i),'cd '+cwd,f'C:\\DCOMPILE {i} >RESULT.TXT','if errorlevel 1 goto failed']
 commands+=['cd \\','echo PASS>PASS.TXT','exit',':failed','cd \\','echo FAIL>FAIL.TXT','exit']
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nset PCPLUS=\n'+'\n'.join(commands)+'\n';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=150)
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(NAMES[i],(c/'RESULT.TXT').read_text()) for i,c in enumerate(cases) if (c/'RESULT.TXT').exists()]
 reports=[]
 for i,case in enumerate(cases):
  mode,checks,status,execs,held,opens,closes,installed=struct.unpack('<8H',(case/'RESULT.BIN').read_bytes());assert mode==i
  state=(case/'STATE.BIN').read_bytes();bundle=(case/'BUNDLE.BIN').read_bytes();assert len(state)==256 and len(bundle)==2024
  if status==0:
   path=('C:\\'+str((case/'GO.ASX').relative_to(out)).replace('/',chr(92))).encode()
   assert (case/'GO.ASX').read_bytes()==expected
   assert bundle[1948:]==path.ljust(64,b'\0')+struct.pack('<HHII',1,expected[0],len(expected),zlib.crc32(expected))
  if i not in (2,11):assert (case/'GO.ASP').read_bytes()==(b'proc main\nBAD BAD BAD\nendproc\n' if i==1 else source)
  if i==3:assert (case/'GO.ASX').read_bytes()==b'SENTINEL'
  if i in (1,2,4,5,7,8,10,12):assert not (case/'GO.ASX').exists()
  if i in (9,11,13,14):assert (case/'GO.ASX').exists()
  reports.append(dict(case=NAMES[i],passed=True,native_assertions=checks,status=status,EXEC_requests=execs,held=bool(held),installed=installed,opens=opens,closes=closes))
 assert not list(out.rglob('RAN'))
 result=dict(passed=True,binary_sha256=m['binary_sha256'],fault_child_sha256=m['fault_child_sha256'],compiler_binary_sha256=cm['binary_sha256'],compiler_sources=cm['sources'],sources=m['sources'],case_count=len(reports),cases=reports,native_assertions=sum(c['native_assertions'] for c in reports),original_inputs=[],test_sources={n:sha(ROOT/n) for n in ['standalone/test_directory_compile_dos.py','src/aspect/compiler.py']},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Production owner/readers, actual DOS spawning adapter for the component, true compiler for acceptance and a separately identified executable for fault cases. Actual parent process_run/UART/memory handoff is tested separately.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(reports),'compile owner DOS workflows,',result['native_assertions'],'assertions')
if __name__=='__main__':main()
