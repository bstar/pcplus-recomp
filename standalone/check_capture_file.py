#!/usr/bin/env python3
"""Source-only actual DOS binary capture sink plus compiled FS failure cases."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/capture-file';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/capture/capture_file.c',ROOT/'src/capture/capture_reservation.c',ROOT/'standalone/capture_file_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/capture')]
  for name,flags,sources in [('CAPTURE.EXE',[],common+[ROOT/'src/capture/capture_fs.c']),('CAPFAULT.EXE',['-dCF_FAULT'],common)]:
   subprocess.run(base+flags+['-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for name in ['CAPTURE.EXE','CAPFAULT.EXE']:shutil.copy2(out/name,run/name)
  commands='\n'.join(f'{cmd} > {label}.TXT\nif errorlevel 1 goto failed\necho PASS>{label}.OK' for label,cmd in [('NORMAL','CAPTURE'),('FAULT','CAPFAULT'),('SEEKFAIL','CAPFAULT S'),('WRFAIL','CAPFAULT W')])
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
  labels=['NORMAL','FAULT','SEEKFAIL','WRFAIL'];logs={n:(run/(n+'.TXT')).read_text(errors='replace') if (run/(n+'.TXT')).exists() else '' for n in labels}
  checks={'DOS_normal_fault_and_compound_exit':process.returncode==0 and all((run/(n+'.OK')).exists() for n in labels) and not (run/'FAIL.TXT').exists()}
  for label,minimum in [('NORMAL',17),('FAULT',30),('SEEKFAIL',4),('WRFAIL',5)]:checks[label+'_cases']=logs[label].count('PASS ')>=minimum and 'FAIL ' not in logs[label]
  block=bytes((i*37+19)%256 for i in range(32768))
  for name,want in {'BINARY.BIN':block*2+block[:137]+block[:1024]+block[:128],'DATA/LOG.BIN':block[:128],'READONLY.BIN':b'preserve','ZERO.BIN':b'','REL.BIN':block[:1]}.items():
   checks[name]=(run/name).is_file() and (run/name).read_bytes()==want
  checks['missing_append_never_created']=not (run/'MISSING.BIN').exists()
  sources=set(common+[ROOT/'src/capture/capture_fs.c',ROOT/'src/capture/capture_file.h',ROOT/'src/capture/capture_reservation.h',ROOT/'src/capture/capture_fs.h',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'cases':{n:logs[n].splitlines() for n in labels},'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['CAPTURE.EXE','CAPFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'scope':'Maintained exact binary foreground DOS sink: exclusive NEW or existing APPEND on one write-only seek-END handle; actual DOS normal filesystem and compiled kernel fault boundaries. No formatting/native FILE interoperability, runtime integration, concurrent-writer guarantee, deletion/rollback or crash atomicity.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
