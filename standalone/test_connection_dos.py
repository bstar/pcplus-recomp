#!/usr/bin/env python3
"""Actual DOS automatic dial/control against a synthetic serial modem peer."""
import hashlib,json,os,socket,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def run(name,mode,keys):
 out=ROOT/'build/connection-dos'/name;out.mkdir(parents=True,exist_ok=True)
 for p in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):(out/p).unlink(missing_ok=True)
 payload=fixture(timeout=2 if mode=='silence' else 5)
 (out/'TEST.PRM').write_bytes(payload)
 (out/'sampler.asm').write_text(SAMPLER)
 subprocess.run(['nasm','-f','bin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(5)
 wire=bytearray();commands=[];errors=[];stop=threading.Event();checks={};attempts=0
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.05);line=bytearray();online=False
    while not stop.is_set():
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block)
     for byte in block:
      if online:
       line.append(byte)
       if line.endswith(b'+++~'):raise AssertionError('Pause marker reached physical wire')
       if line.endswith(b'+++ATH\r'):
        checks['configured_hangup_reached_wire']=True;conn.sendall(b'\r\nOK\r\n');line.clear();online=False
       continue
      if byte==27:line.clear();checks['configured_abort_reached_wire']=True;continue
      if byte!=13:line.append(byte);continue
      command=bytes(line);commands.append(command.decode('ascii','replace'));line.clear()
      if command==b'ATZ':conn.sendall(b'\r\nOK\r\n')
      elif command==b'ATDCaseTest:23':
       attempts+=1
       if mode=='silence':continue
       if mode=='busy' or (mode=='redial' and attempts==1):conn.sendall(b'\r\nBUSY\r\n');continue
       online=True
       # Same TCP write as CONNECT: prove main retains bytes after a match
       # while the sender finishes its final inter-character delay.
       conn.sendall(b'CONNECT\r\n\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
      else:checks['unexpected_modem_command']=True
  except (OSError,AssertionError) as error:errors.append(str(error))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
[autoexec]
@echo off
mount c "{BINARY.parent}"
mount d "{out}"
c:
D:\\SNAP B
ADDKEY {keys}
TERMINAL @D:\\TEST.PRM /D:CaseTest:23
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
''';(out/'dosbox.conf').write_text(cfg)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();started=time.monotonic()
 with (out/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
 stop.set();server.close();thread.join(1)
 before=(out/'BEFORE.BIN').read_bytes() if (out/'BEFORE.BIN').exists() else b''
 after=(out/'AFTER.BIN').read_bytes() if (out/'AFTER.BIN').exists() else b''
 screen=(out/'SCREEN.BIN').read_bytes() if (out/'SCREEN.BIN').exists() else b''
 checks.update({'DOS_normal_exit':result.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'hardware_restored':len(before)==42 and before==after,'PRM_unchanged':(out/'TEST.PRM').read_bytes()==payload,'binary_unchanged':digest==hashlib.sha256(BINARY.read_bytes()).hexdigest(),'no_peer_errors':not errors,'no_unexpected_commands':not checks.pop('unexpected_modem_command',False),'actual_init_and_dial':commands[:2]==['ATZ','ATDCaseTest:23']})
 if mode in ('success','hangup','redial'):
  checks['actual_DOS_CPR']=b'\x1b[1;16R' in wire
  checks['actual_DOS_DA']=b'\x1b[?1;2c' in wire
  checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'
 if mode=='redial':checks['second_configured_attempt']=commands==['ATZ','ATDCaseTest:23','ATZ','ATDCaseTest:23']
 if mode=='hangup':checks['configured_hangup_reached_wire']=bool(checks.get('configured_hangup_reached_wire'))
 if mode in ('busy','silence'):checks['configured_abort_reached_wire']=bool(checks.get('configured_abort_reached_wire'))
 (out/'serial.bin').write_bytes(wire)
 (out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 proof={'case':name,'passed':all(checks.values()),'checks':checks,'commands':commands,'errors':errors,'seconds':round(time.monotonic()-started,3),'binary_sha256':digest,'scope':'Actual DOS main/controller/sender/UART/keyboard/ANSI replies and video, synthetic serial modem. Same-write CONNECT+banner, no injected terminal replies. Physical DCD/CTS not represented.'}
 (out/'result.json').write_text(json.dumps(proof,indent=2)+'\n');print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True);return proof
def main():
 cases=[('fast-connect-banner','success','p4000 a-x'),('busy-abort','busy','p4000 a-x'),('timeout-abort','silence','p4000 a-x'),('configured-hangup','hangup','p3000 a-h p2200 a-x'),('explicit-redial','redial','p3500 a-d p3500 a-x')]
 results=[run(*case) for case in cases]
 summary={'passed':all(r['passed'] for r in results),'cases':results,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest()}
 (ROOT/'build/connection-dos/result.json').write_text(json.dumps(summary,indent=2)+'\n')
 return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
