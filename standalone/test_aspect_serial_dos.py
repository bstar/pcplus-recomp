#!/usr/bin/env python3
"""Actual DOS recovered IRQ driver and maintained child lease on loopback UART."""
import hashlib,json,os,socket,subprocess,threading
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-serial';BINARY=OUT/'SERIAL.EXE'
def run(flow,cancel=False,dtr=True):
 name='dos-'+flow+('-cancel' if cancel else '')+('-denied' if not dtr else '')
 folder=OUT/name;folder.mkdir(exist_ok=True)
 for n in ['PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN']:(folder/n).unlink(missing_ok=True)
 (folder/'snap.asm').write_text(SAMPLER)
 (folder/'setup.asm').write_text('BITS16\nORG100h\nmov dx,3fbh\nmov al,80h\nout dx,al\nmov dx,3f8h\nmov al,12\nout dx,al\ninc dx\nxor al,al\nout dx,al\nmov dx,3fbh\nmov al,3\nout dx,al\nmov dx,3fch\nmov al,'+('1' if dtr else '0')+'\nout dx,al\nmov ax,4c00h\nint21h\n'.replace('BITS16','BITS 16').replace('ORG100h','ORG 100h').replace('int21h','int 21h'))
 # Keep generated assembly readable and independent of product code.
 source=(folder/'setup.asm').read_text().replace('BITS16','BITS 16').replace('ORG100h','ORG 100h').replace('int21h','int 21h');(folder/'setup.asm').write_text(source)
 for base in ['snap','setup']:subprocess.run(['nasm','-fbin',str(folder/(base+'.asm')),'-o',str(folder/(base+'.COM'))],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(10);wire=bytearray();errors=[]
 def peer():
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(10);sent=False
    while True:
     data=conn.recv(4096)
     if not data:break
     wire.extend(data)
     if b'D' in wire and not sent and not cancel:conn.sendall(bytes([0,0x1a,0x80,0xff]));sent=True
  except (OSError,TimeoutError) as e:errors.append(str(e))
 t=threading.Thread(target=peer);t.start()
 expected=0 if dtr else 4
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{OUT}"
mount d "{folder}"
d:
SETUP
SNAP B
{'ADDKEY p800 escape p5000 space' if cancel else 'ADDKEY p6000 space'}
c:\\SERIAL /S1:0003:03:{flow} >RESULT.TXT
if errorlevel {expected+1} goto fail
if errorlevel {expected} goto pass
:fail
echo FAIL>FAIL.TXT
goto done
:pass
echo PASS>PASS.TXT
:done
pause >nul
SNAP A
exit
'''
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=15)
 t.join(1);server.close()
 checks=dict(expected_DOS_exit=p.returncode==0 and (folder/'PASS.TXT').exists() and not(folder/'FAIL.TXT').exists(),hardware_restored=len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes(),wire_exact=bytes(wire)==(b'' if not dtr else (b'\x11' if flow in ['S','B'] else b'')+b'D'+(b'' if cancel else b'R')+(b'\x13' if flow in ['S','B'] else b'')),no_peer_error=not errors)
 result=dict(case=name,passed=all(checks.values()),checks=checks,errors=errors,wire_hex=wire.hex());(folder/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True);assert result['passed'];return result

def main():
 cases=[run(f) for f in ['N','S','H','B']]+[run('N',cancel=True),run('N',dtr=False)]
 result=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),original_inputs=[],limitations=['DOSBox-X nullmodem, virtual CTS always ready; physical modem/flow timing unverified.','Independent backend diagnostic; live parent ASIO handback tested separately.'])
 (OUT/'dos-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
