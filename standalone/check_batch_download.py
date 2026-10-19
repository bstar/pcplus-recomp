#!/usr/bin/env python3
"""Build/run actual DOS batch-file owner and deterministic compiled FS faults."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/batch-download';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  common=[ROOT/'src/transfer/batch_download.c',ROOT/'src/transfer/batch_header.c',ROOT/'src/transfer/download_file.c',ROOT/'standalone/batch_download_host.c']
  base=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/transfer')]
  for name,flags,sources in [('BATCHDL.EXE',[],common+[ROOT/'src/transfer/download_fs.c']),('BDFAULT.EXE',['-dBD_FAULT'],common)]:
   subprocess.run(base+flags+['-fe='+name]+list(map(str,sources)),cwd=out,check=True)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for name in ['BATCHDL.EXE','BDFAULT.EXE']:shutil.copy2(out/name,run/name)
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
BATCHDL > NORMAL.TXT
if errorlevel 1 goto failed
echo PASS>NORMAL.OK
BDFAULT > FAULT.TXT
if errorlevel 1 goto failed
echo PASS>FAULT.OK
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
  (out/'dosbox.conf').write_text(config)
  with (out/'dosbox.log').open('w') as log:
   process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  logs={n:(run/n).read_text(errors='replace') if (run/n).exists() else '' for n in ['NORMAL.TXT','FAULT.TXT']}
  payload=bytes((i*37+19)%256 for i in range(1024))
  checks={'normal_and_fault_DOS_exit':process.returncode==0 and all((run/n).exists() for n in ['NORMAL.OK','FAULT.OK']) and not (run/'FAIL.TXT').exists(),
   'normal_cases':logs['NORMAL.TXT'].count('PASS ')>=15 and 'FAIL ' not in logs['NORMAL.TXT'],
   'fault_cases':logs['FAULT.TXT'].count('PASS ')>=29 and 'FAIL ' not in logs['FAULT.TXT']}
  for path,expected in {'DATA/BIG.BIN':payload*65+payload[:1],'DATA/ZERO.BIN':b'','DATA/UNKNOWN.BIN':payload+payload[:128],'DATA/PCRX.$$$':b'foreign','ROOT.BIN':payload[:1],'HERE.BIN':payload[:1],'EXACT.BIN':payload[:3]}.items():
   checks[path]=(run/path).is_file() and (run/path).read_bytes()==expected
  checks['only_foreign_stage_remains']=not (run/'PCRX.$$$').exists() and not any((run/'DATA'/n).exists() for n in ['LATER.BIN','FOREIGN.BIN'])
  sources=set(common+[ROOT/'src/transfer/download_fs.c',ROOT/'src/transfer/batch_download.h',ROOT/'src/transfer/batch_header.h',ROOT/'src/transfer/download_file.h',ROOT/'src/transfer/download_fs.h',Path(__file__).resolve()])
  result={'passed':all(checks.values()),'checks':checks,'normal_cases':logs['NORMAL.TXT'].splitlines(),'fault_cases':logs['FAULT.TXT'].splitlines(),'binaries':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['BATCHDL.EXE','BDFAULT.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},'scope':'Actual DOSBox-X8086 source-built maintained per-file batch storage owner with real codec and exact-write/checked-close/no-overwrite backend; normal DOS files and compiled FS fault boundaries. No UART/protocol framing, original binary, full batch engine or crash atomicity claim.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
