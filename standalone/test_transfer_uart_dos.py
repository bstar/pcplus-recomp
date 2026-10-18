#!/usr/bin/env python3
"""Actual DOS recovered timed receive/bulk transmit via loopback nullmodem."""
import fcntl,hashlib,json,os,socket,subprocess,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-uart-dos';BINARY=ROOT/'build/transfer-uart/TUART.EXE'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name in ['PASS.TXT','FAIL.TXT']:(OUT/name).unlink(missing_ok=True)
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(12);wire=bytearray();errors=[]
  def peer():
   try:
    conn,_=server.accept()
    with conn:
     conn.settimeout(8);time.sleep(0.7);conn.sendall(b'Z')
     while len(wire)<1024:
      data=conn.recv(2048)
      if not data:break
      wire.extend(data)
     if len(wire)==1024:conn.sendall(b'\xa5')
   except Exception as e:errors.append(str(e))
   finally:server.close()
  thread=threading.Thread(target=peer);thread.start()
  conf=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{BINARY.parent}"
mount d "{OUT}"
c:
TUART
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto done
:fail
echo FAIL>D:\\FAIL.TXT
:done
exit
'''
  (OUT/'dosbox.conf').write_text(conf);digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
  with (OUT/'dosbox.log').open('w') as log:
   try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=15).returncode
   except subprocess.TimeoutExpired:code=-1
  thread.join(12);(OUT/'wire.bin').write_bytes(wire)
  checks={'DOS_selfcheck':code==0 and (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),'all_binary_bytes_exact':wire==bytes(range(256))*4,'peer_completed':not errors and not thread.is_alive(),'frozen_binary':hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest}
  proof={'passed':all(checks.values()),'checks':checks,'errors':errors,'binary_sha256':digest,'scope':'Actual DOS8086 recovered UART IRQ/timed-reader/bulk-writer plus exact DOS clock and bounded extent guard; loopback binary1024 bytes including00/ff and acknowledgement. NONEflow only; no physicaladapter/CTSstalls, vendorUI or full transfer session.'};(OUT/'result.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
