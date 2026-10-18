#!/usr/bin/env python3
"""Actual DOS two-owner canonical exclusion and independent kernel faults."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/capture-owners';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/capture/capture_file.c',ROOT/'standalone/capture_owners_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/capture')]
  for name,flags,sources in [('OWNERS.EXE',[],common+[ROOT/'src/capture/capture_fs.c']),('OWFAULT.EXE',['-dOWNERS_FAULT'],common)]:
   subprocess.run(base+flags+['-fm='+name+'.map','-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for n in ['OWNERS.EXE','OWFAULT.EXE']:shutil.copy2(out/n,run/n)
  recipes=[('NORMAL','OWNERS'),('GUARDS','OWFAULT'),('CAPKEEP','OWFAULT C'),('CAPDROP','OWFAULT D'),('SNAPKEEP','OWFAULT S'),('SNAPDROP','OWFAULT T')]
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
  for n,want in {'TEXT.LOG':b'T\0\x1aEND','SNAP.BIN':b'S\xff\r\n','SAME.LOG':b'W','INDEPEND.BIN':b'I','DATA/INNER.LOG':b'N'}.items():checks[n]=(run/n).is_file() and (run/n).read_bytes()==want
  sources=set(common+[ROOT/'src/capture/capture_fs.c',ROOT/'src/capture/capture_file.h',ROOT/'src/capture/capture_fs.h',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'cases':{n:logs[n].splitlines() for n,_ in recipes},'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['OWNERS.EXE','OWFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'static_state_bytes':690,'snapshot_abi_bytes':96,'owner_descriptor_bytes':134,'minimum_kernel_contract':'DOS3+ INT21/60h canonical identity into128-byte buffer; exclusive NEW INT21/5Bh; APPEND write-only3Dh and samehandle4202h','scope':'Actual DOSBox-X8086 two independent checked binary owners, relative/drive-relative/absolute/current-directory canonical collision tests; compiled kernel faults for malformed identities and ambiguous close on either owner whether kernel kept/released handle. DOS canonical identity is not an external-process lock, host-mount/inode proof or concurrent namespace-remapping guarantee.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
