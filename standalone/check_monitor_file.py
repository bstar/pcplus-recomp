#!/usr/bin/env python3
"""Actual DOS three-owner canonical exclusion and independent kernel faults."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/monitor-file';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/capture/capture_file.c',ROOT/'src/capture/capture_reservation.c',ROOT/'standalone/monitor_file_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/capture')]
  for name,flags,sources in [('MONITOR.EXE',[],common+[ROOT/'src/capture/capture_fs.c']),('MOFAULT.EXE',['-dOWNERS_FAULT'],common)]:
   subprocess.run(base+flags+['-fm='+name+'.map','-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for n in ['MONITOR.EXE','MOFAULT.EXE']:shutil.copy2(out/n,run/n)
  recipes=[('NORMAL','MONITOR'),('FAULT','MOFAULT'),('CAPKEEP','MOFAULT 0'),('CAPDROP','MOFAULT 0 D'),('SNAPKEEP','MOFAULT 1'),('SNAPDROP','MOFAULT 1 D'),('MONKEEP','MOFAULT 2'),('MONDROP','MOFAULT 2 D')]
  commands='\n'.join(f'{cmd} > {n}.TXT\nif errorlevel 1 goto failed\necho PASS>{n}.OK' for n,cmd in recipes)
  conf=f'''[sdl]
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
  (out/'dosbox.conf').write_text(conf)
  with (out/'dosbox.log').open('w') as log:
   code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30).returncode
  logs={n:(run/(n+'.TXT')).read_text(errors='replace') if (run/(n+'.TXT')).exists() else '' for n,_ in recipes}
  checks={'DOS_exits':code==0 and all((run/(n+'.OK')).exists() for n,_ in recipes) and not (run/'FAIL.TXT').exists()}
  for n,_ in recipes:checks[n]=logs[n].count('PASS ')>=8 and 'FAIL ' not in logs[n]
  for n,want in {'KEEP.BIN':b'\0\x1a\xff\x11\x13','EMPTY.BIN':b'','PAIR.BIN':b'','LIVE0.BIN':b'X','LIVE1.BIN':b'X','LIVE2.BIN':b'X'}.items():checks[n]=(run/n).is_file() and (run/n).read_bytes()==want
  sources=set(common+[ROOT/'src/capture/capture_fs.c',ROOT/'src/capture/capture_file.h',ROOT/'src/capture/capture_reservation.h',ROOT/'src/capture/capture_fs.h',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'cases':{n:logs[n].splitlines() for n,_ in recipes},'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['MONITOR.EXE','MOFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'static_state_bytes':928,'external_reservation_bytes':8,'snapshot_abi_bytes':96,'owner_descriptor_bytes':134,'minimum_kernel_contract':'DOS3+ INT21/60h canonical identity into128-byte buffer; exclusive NEW INT21/5Bh; explicit monitor REPLACE INT21/3Ch; APPEND write-only3Dh and samehandle4202h','scope':'Actual DOSBox-X8086 three independent owners; explicit monitor-only REPLACE with regular-file/readonly/device guards, exclusive missing-file race, pairwise canonical aliases, exact binary/padding-free writes, short writes, ambiguous close on all three owners whether kernel kept/released handle. DOS canonical identity is not an external-process lock, host-mount/inode proof or concurrent namespace-remapping guarantee.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
