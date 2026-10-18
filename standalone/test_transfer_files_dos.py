#!/usr/bin/env python3
"""Run recovered CRT against real DOS files; no original install inputs."""
import fcntl,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 output=ROOT/'build/transfer-files-dos';output.mkdir(parents=True,exist_ok=True)
 binary=ROOT/'build/transfer-files/FILES.EXE';digest=hashlib.sha256(binary.read_bytes()).hexdigest();cases=[]
 with (output/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name,mode in [('borrowed-binary','B'),('unbuffered-binary','U'),('borrowed-text-CRLF','T'),('closed-handle-errors','F')]:
   folder=output/name;folder.mkdir(parents=True,exist_ok=True)
   for file in ['PASS.TXT','FAIL.TXT','OWNED.BIN']:(folder/file).unlink(missing_ok=True)
   config=f'''[sdl]
output=surface
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
mount c "{binary.parent}"
mount d "{folder}"
d:
c:\\FILES {mode}
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto done
:failed
echo FAIL>D:\\FAIL.TXT
:done
exit
'''
   (folder/'dosbox.conf').write_text(config);env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
   with (folder/'dosbox.log').open('w') as log:
    try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=env,stdout=log,stderr=log,timeout=15).returncode
    except subprocess.TimeoutExpired:code=-1
   expected=bytes(i&255 for i in range(600));expected=expected.replace(b'\n',b'\r\n') if mode=='T' else b'' if mode=='F' else expected
   passed=code==0 and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists() and (folder/'OWNED.BIN').exists() and (folder/'OWNED.BIN').read_bytes()==expected
   cases.append({'case':name,'passed':passed,'returncode':code,'expected_bytes':len(expected)});print(name,'PASS' if passed else 'FAIL',flush=True)
 result={'passed':all(c['passed'] for c in cases),'binary_sha256':digest,'cases':cases,'scope':'Actual source-only native CRT fwrite/fflush/fclose through real DOS40/3e, borrowed512-byte buffer or unbuffered,600 binary/text bytes, reopen/read/EOF and closed-handle errors. No live UART, transaction or whole transfer session.'};(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
