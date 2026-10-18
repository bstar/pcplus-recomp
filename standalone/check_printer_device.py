#!/usr/bin/env python3
"""Actual DOS checked PRN owner with explicit mocked kernel faults."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,struct
ROOT=Path(__file__).resolve().parents[1]
def segments(path):
 data=path.read_bytes();pos=0;names=[''];result={}
 def index(d,j):
  v=d[j]
  return (((v&127)<<8)|d[j+1],j+2) if v&128 else (v,j+1)
 while pos<len(data):
  tag=data[pos];size=struct.unpack_from('<H',data,pos+1)[0];d=data[pos+3:pos+2+size];pos+=size+3
  if tag==0x96:
   j=0
   while j<len(d):n=d[j];j+=1;names.append(d[j:j+n].decode());j+=n
  if tag==0x98:
   j=1 if d[0]&0xe0 else 4
   size=struct.unpack_from('<H',d,j)[0];j+=2;name,j=index(d,j);cls,j=index(d,j)
   result[names[name]]={'class':names[cls],'bytes':size}
 return result
def main():
 out=ROOT/'build/printer-device';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/printer/printer_device.c',ROOT/'standalone/printer_device_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/printer')]
  for name,flags,sources in [('PRINTER.EXE',[],common)]:
   subprocess.run(base+flags+['-fm='+name+'.map','-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-fo=printer_fs.o',str(ROOT/'src/printer/printer_fs.c')],cwd=out,check=True)
  module_segments={n:segments(out/(n+'.o')) for n in ['printer_device','printer_fs']}
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for n in ['PRINTER.EXE']:shutil.copy2(out/n,run/n)
  recipes=[('NORMAL','PRINTER'),('CLOSE','PRINTER C'),('BOTH','PRINTER B')]
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
  for n,_ in recipes:checks[n]=logs[n].count('PASS ')>=6 and 'FAIL ' not in logs[n]
  sources=set(common+[ROOT/'src/printer/printer_device.h',ROOT/'src/printer/printer_fs.h',ROOT/'src/printer/printer_fs.c',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'cases':{n:logs[n].splitlines() for n,_ in recipes},'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['PRINTER.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'module_segments':module_segments,'static_state_bytes':36,'snapshot_abi_bytes':32,'minimum_kernel_contract':'DOS openPRN write-only3D,4400/4401 character/raw info withDH0,4407 readiness,40h exactbyte,3Eh close','scope':'Actual8086 DOS execution of checked source device owner with explicit mocked DOS kernel boundaries; no actual PRN driver or physical output exercised. Driver calls are not timing bounded. Reference https://www.pcjs.org/documents/books/mspl13/msdos/dosref33/'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
