#!/usr/bin/env python3
"""Independent actual DOS compiled processed-capture owner and FS fault checks."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/capture-session';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/capture/capture_session.c',ROOT/'src/capture/capture_file.c',ROOT/'standalone/capture_session_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/capture')]
  for name,flags,sources in [('CAPSESS.EXE',[],common+[ROOT/'src/capture/capture_fs.c']),('CSFAULT.EXE',['-dCS_FAULT'],common)]:
   subprocess.run(base+flags+['-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for name in ['CAPSESS.EXE','CSFAULT.EXE']:shutil.copy2(out/name,run/name)
  recipes=[('NORMAL','CAPSESS'),('GUARDS','CSFAULT'),('SHORT','CSFAULT S'),('WRITE','CSFAULT W'),('CLOSE','CSFAULT C'),('COMPOUND','CSFAULT X'),('CRFAIL','CSFAULT R'),('SEEK','CSFAULT Q'),('PAUSE','CSFAULT P'),('TIMER','CSFAULT T')]
  commands='\n'.join(f'{cmd} > {label}.TXT\nif errorlevel 1 goto failed\necho PASS>{label}.OK' for label,cmd in recipes)
  config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{run}"
c:
{commands}
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
  (out/'dosbox.conf').write_text(config)
  with (out/'dosbox.log').open('w') as log:
   process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  logs={n:(run/(n+'.TXT')).read_text(errors='replace') if (run/(n+'.TXT')).exists() else '' for n,_ in recipes}
  checks={'all_DOS_normal_fault_exit':process.returncode==0 and all((run/(n+'.OK')).exists() for n,_ in recipes) and not (run/'FAIL.TXT').exists()}
  for n,_ in recipes:checks[n+'_checks']=bool(logs[n].count('PASS ')>=3 and 'FAIL ' not in logs[n])
  expected={'TEXT.LOG':b'A\r\n\r\0\xff\x7f\r\nB\r\nC','BOUND.LOG':b'x'*255+b'\r\n'+b'y'*254,'TIMED.LOG':b'TU','CLOCK.LOG':b'M','PCPLUS.LOG':b'\r','READONLY.LOG':b'KEEP'}
  for name,want in expected.items():checks[name]=(run/name).is_file() and (run/name).read_bytes()==want
  checks['invalid_before_init_created_no_file']=not (run/'EARLY.LOG').exists()
  sources=set(common+[ROOT/'src/capture/capture_fs.c',ROOT/'src/capture/capture_session.h',ROOT/'src/capture/capture_file.h',ROOT/'src/capture/capture_fs.h',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'cases':{n:logs[n].splitlines() for n,_ in recipes},'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['CAPSESS.EXE','CSFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'scope':'Independent actual DOSBox-X8086 compilation of maintained capture_session and binary file owner. Real normal files; compiled filesystem boundary faults. API clock vectors include18ticks/midnight; no native09b6 filtering, live UART, terminal integration, physicaldisk failure or native capture equivalence claim.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
