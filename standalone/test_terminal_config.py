#!/usr/bin/env python3
"""Run actual PRM startup, CLI precedence and rejection in DOSBox-X."""
import fcntl,hashlib,json,os,socket,subprocess,threading,time
from pathlib import Path
from test_terminal import SAMPLER
from terminal_config_fixtures import image,change,BASES
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def run(name,payload,arguments,*,com=2,profile=6,attribute=0x1e,expected=0,ready=True):
 out=ROOT/'build/terminal-config-tests'/name;out.mkdir(parents=True,exist_ok=True)
 for file in ['PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','TEST.PRM']:(out/file).unlink(missing_ok=True)
 if payload is not None:(out/'TEST.PRM').write_bytes(payload)
 base=BASES[com-1];sampler=SAMPLER
 for offset in [0,1,3,4]:sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (out/'sampler.asm').write_text(sampler)
 subprocess.run(['nasm','-f','bin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 peer_checks={};wire=bytearray();stop=threading.Event();errors=[]
 server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(3)
 def peer():
  try:
   conn,_=server.accept()
   with conn:
    conn.settimeout(.05);pending=bytearray()
    def receive(token,timeout=.35):
     end=time.monotonic()+timeout
     while time.monotonic()<end and not stop.is_set():
      if token in pending:return True
      try:
       block=conn.recv(4096)
       if not block:return False
       pending.extend(block);wire.extend(block)
      except socket.timeout:pass
     return token in pending
    time.sleep(.15)
    if ready:
     for _ in range(5):
      conn.sendall(b'\x1b[5n')
      if receive(b'\x1b[0n'):break
     peer_checks['actual_ready_reply']=b'\x1b[0n' in pending
     if not peer_checks['actual_ready_reply']:return
     conn.sendall(b'\x1b[0c')
     peer_checks['imported_profile_device_reply']=receive(b'\x1b[?62;2c' if profile==4 else b'\x1b[?1;2c')
     conn.sendall(b'\x1b[2J\x1b[HCFG READY')
     conn.sendall(b'\x1b[6n')
     peer_checks['rendered_cursor_reply']=receive(b'\x1b[1;10R')
    while not stop.wait(.02):pass
  except (OSError,TimeoutError) as e:errors.append(str(e))
 thread=threading.Thread(target=peer,daemon=True);thread.start()
 serial='\n'.join(f'serial{i}='+ (f'nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1' if i==com else 'disabled') for i in range(1,5))
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
c:
D:\\SNAP B
ADDKEY p2000 a-x
TERMINAL {arguments}
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
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 with (out/'dosbox.log').open('w') as log:
  p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=12)
 stop.set();server.close();thread.join(1)
 before=(out/'BEFORE.BIN').read_bytes() if (out/'BEFORE.BIN').exists() else b''
 after=(out/'AFTER.BIN').read_bytes() if (out/'AFTER.BIN').exists() else b''
 screen=(out/'SCREEN.BIN').read_bytes() if (out/'SCREEN.BIN').exists() else b''
 checks={'expected_DOS_exit':p.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'IRQ_UART_PIC_restored':len(before)==42 and before==after,'screen_captured':len(screen)==4000,'requested_file_unchanged':(not (out/'TEST.PRM').exists()) if payload is None else (out/'TEST.PRM').read_bytes()==payload,'binary_unchanged':digest==hashlib.sha256(BINARY.read_bytes()).hexdigest()}
 if ready:
  checks.update(peer_checks)
  checks['actual_imported_video_color']=screen[:18]==b''.join(bytes([x,attribute]) for x in b'CFG READY')
  checks['all_protocol_checks_seen']=len(peer_checks)==3
 (out/'screen.txt').write_text('\n'.join(screen[row*160:row*160+160:2].decode('cp437') for row in range(25))+'\n')
 (out/'serial.bin').write_bytes(wire)
 result={'case':name,'passed':all(checks.values()),'checks':checks,'binary_sha256':digest,'command':arguments,'expected_exit':expected,'observed_errors':errors,'scope':'Actual source-built terminal DOS startup with synthetic partial PRM; actual UART/IRQ, device/cursor replies and video. File and hardware independently checked.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(name,'PASS' if result['passed'] else 'FAIL',flush=True);return result

def main():
 out=ROOT/'build/terminal-config-tests';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  cases=[
   ('import-ANSI-COM2',image(),'@D:\\TEST.PRM',{}),
   ('import-VT220',image(profile=4),'@D:\\TEST.PRM',{'profile':4}),
   ('CLI-all-overrides',image(baud=8,parity=2,bits=7,stop=2,profile=4),'@D:\\TEST.PRM COM1 38400 8N1 SOFT',{'com':1,'profile':4}),
   ('import-both-flow',image(soft=1,hard=1),'@D:\\TEST.PRM',{}),
   ('import-115200-COM3',image(port=3,baud=8),'@D:\\TEST.PRM',{'com':3}),
   ('missing-file',None,'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('short-file',image()[:17],'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('long-file',image()+b'X','@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('invalid-profile',change(image(),0x194,7),'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('invalid-flow',change(image(),0x198,2),'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('invalid-IRQ',change(image(),0x186,5),'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('invalid-display',change(image(),0x1ae,256),'@D:\\TEST.PRM',{'expected':7,'ready':False}),
   ('bad-file-not-hidden-by-CLI',change(image(),0,7),'@D:\\TEST.PRM COM1 38400 NONE',{'com':1,'expected':7,'ready':False}),
   ('help-does-not-load-missing',None,'@D:\\TEST.PRM /?',{'expected':0,'ready':False}),
   ('invalid-CLI',image(),'@D:\\TEST.PRM BADOPTION',{'expected':1,'ready':False}),
  ]
  results=[run(name,data,args,**options) for name,data,args,options in cases]
  summary={'passed':all(r['passed'] for r in results),'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':results,'scope':'Actual DOS PRM startup/import, CLI precedence, no-rewrite error handling and independent hardware/video/protocol checks. Synthetic fixtures only; not full schema/default generation.'}
  (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
