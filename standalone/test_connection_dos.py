#!/usr/bin/env python3
"""Actual DOS automatic dial/control against a synthetic serial modem peer."""
import hashlib,json,os,socket,subprocess,threading,time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
from directory_test_support import accounting_check
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def run(name,mode,keys,*,directory=None,prm=None,arguments=None,com=1,profile=6,target=b'CaseTest:23',expected=0,directory_entry=1,directory_expected=None,accounting_delta=None,recovery_conflict=False,files=None,banner=None,working_drive="c",environment=None):
 assert working_drive in ("c","d")
 out=ROOT/'build/connection-dos'/name;out.mkdir(parents=True,exist_ok=True)
 for p in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):(out/p).unlink(missing_ok=True)
 # These are owned synthetic fixture directories, never a user's directory.
 for p in ('PCPSTG.$$$','PCPBAK.$$$'):(out/p).unlink(missing_ok=True)
 if recovery_conflict:(out/'PCPBAK.$$$').write_bytes(b'SYNTHETIC RECOVERY CONFLICT')
 payload=prm if prm is not None else fixture(timeout=2 if mode=='silence' else 5)
 (out/'TEST.PRM').write_bytes(payload)
 if directory is not None:(out/'TEST.DIR').write_bytes(directory)
 for filename,data in (files or {}).items():
  relative=Path(filename)
  assert relative.parts and not relative.is_absolute() and '..' not in relative.parts and '\\' not in filename and filename not in ('TEST.DIR','TEST.PRM')
  target_file=out/relative;target_file.parent.mkdir(parents=True,exist_ok=True);target_file.write_bytes(data)
 environment_lines=['set PCPLUS=']
 for variable,value in (environment or {}).items():
  assert variable and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in variable)
  assert not any(c in value for c in '\r\n\0%<>|&')
  environment_lines.append('set '+variable+'='+value)
 environment_commands='\n'.join(environment_lines)
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[com-1]
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (out/'sampler.asm').write_text(sampler)
 subprocess.run(['nasm','-f','bin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(5)
 wire=bytearray();commands=[];errors=[];stop=threading.Event();checks={};attempts=0
 def peer():
  nonlocal attempts
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.05);line=bytearray();online=False;probe=bytearray();next_probe=0
    while not stop.is_set():
     if mode=='direct' and not online and time.monotonic()>=next_probe:
      conn.sendall(b'\x1b[5n');next_probe=time.monotonic()+.25
     try:block=conn.recv(4096)
     except socket.timeout:continue
     if not block:break
     wire.extend(block)
     if mode=='direct' and not online:
      probe.extend(block)
      if b'\x1b[0n' in probe:
       checks['actual_direct_ready']=True;online=True
       conn.sendall(b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c')
      continue
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
      elif command==b'ATD'+target:
       attempts+=1
       if mode=='silence':continue
       if mode=='busy' or (mode=='redial' and attempts==1):conn.sendall(b'\r\nBUSY\r\n');continue
       online=True
       # Same TCP write as CONNECT: prove main retains bytes after a match
       # while the sender finishes its final inter-character delay.
       conn.sendall(b'CONNECT\r\n'+(banner if banner is not None else b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'))
      else:checks['unexpected_modem_command']=True
  except (OSError,AssertionError) as error:errors.append(str(error))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 serial='\n'.join(f'serial{i}='+ (f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1' if i==com else 'disabled') for i in range(1,5))
 arguments=arguments or '@D:\\TEST.PRM /D:CaseTest:23'
 branch=(f'if errorlevel {expected+1} goto failed\nif errorlevel {expected} goto expected\ngoto failed' if expected else 'if errorlevel 1 goto failed\ngoto expected')
 cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{serial}
[autoexec]
@echo off
mount c "{BINARY.parent}"
mount d "{out}"
{working_drive}:
{environment_commands}
D:\\SNAP B
ADDKEY {keys}
C:\\TERMINAL {arguments}
{branch}
:expected
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
 checks.update({'DOS_expected_exit':result.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'hardware_restored':len(before)==42 and before==after,'PRM_unchanged':(out/'TEST.PRM').read_bytes()==payload,'binary_unchanged':digest==hashlib.sha256(BINARY.read_bytes()).hexdigest(),'no_peer_errors':not errors,'no_unexpected_commands':not checks.pop('unexpected_modem_command',False)})
 if directory is not None:
  delta=int(mode in ('success','hangup','redial','direct')) if accounting_delta is None else accounting_delta
  checks['directory_expected_updates_only']=accounting_check(directory if directory_expected is None else directory_expected,(out/'TEST.DIR').read_bytes(),directory_entry,delta)
 if recovery_conflict:checks['recovery_file_preserved']=(out/'PCPBAK.$$$').read_bytes()==b'SYNTHETIC RECOVERY CONFLICT'
 for filename,data in (files or {}).items():checks['fixture_unchanged_'+filename]=(out/filename).read_bytes()==data
 if mode in ('direct','reject','cancel'):checks['no_modem_commands']=not commands and (not wire if mode!='direct' else b'ATD' not in wire and b'ATZ' not in wire)
 else:checks['actual_init_and_dial']=commands[:2]==['ATZ',('ATD'+target.decode('ascii'))]
 if mode in ('success','hangup','redial','direct'):
  checks['actual_DOS_CPR']=b'\x1b[1;16R' in wire
  checks['actual_DOS_DA']=(b'\x1b[?62;2c' if profile==4 else b'\x1b[?1;2c') in wire
  checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'
 if mode=='redial':checks['second_configured_attempt']=commands==['ATZ','ATDCaseTest:23','ATZ','ATDCaseTest:23']
 if mode=='hangup':checks['configured_hangup_reached_wire']=bool(checks.get('configured_hangup_reached_wire'))
 if mode in ('busy','silence'):checks['configured_abort_reached_wire']=bool(checks.get('configured_abort_reached_wire'))
 (out/'serial.bin').write_bytes(wire)
 (out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 proof={'case':name,'passed':all(checks.values()),'checks':checks,'commands':commands,'errors':errors,'seconds':round(time.monotonic()-started,3),'binary_sha256':digest,'command':arguments,'expected_exit':expected,'working_drive':working_drive,'environment':environment or {},'scope':'Actual DOS main/controller/sender/UART/keyboard/ANSI replies and video, synthetic serial modem. Same-write CONNECT+banner, no injected terminal replies. Physical DCD/CTS not represented.'}
 (out/'result.json').write_text(json.dumps(proof,indent=2)+'\n');print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True);return proof
def main():
 cases=[('fast-connect-banner','success','p4000 a-x'),('busy-abort','busy','p4000 a-x'),('timeout-abort','silence','p4000 a-x'),('configured-hangup','hangup','p3000 a-h p2200 a-x'),('explicit-redial','redial','p3500 a-d p3500 a-x')]
 results=[run(*case) for case in cases]
 summary={'passed':all(r['passed'] for r in results),'cases':results,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest()}
 (ROOT/'build/connection-dos/result.json').write_text(json.dumps(summary,indent=2)+'\n')
 return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
