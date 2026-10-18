#!/usr/bin/env python3
"""Independent live DOS receive peer: real hotkey/UI, UART and DOS files.

Run only after an explicit terminal freeze. Creates synthetic fixtures exclusively
under ignored build/terminal-transfer-dos, never accesses a mounted DOS drive.
No runtime/product callback or terminal response is injected by this harness.
"""
import argparse,binascii,fcntl,hashlib,json,os,socket,subprocess,threading,time
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/terminal/TERMINAL.EXE'
OUT=ROOT/'build/terminal-transfer-dos'

def payload(count,seed=0):
 """Full blocks: no guessed original filesize or DOS EOF trimming semantics."""
 return bytes((i*37+seed)%256 for i in range(count))
def frame(data,number=1,crc=True):
 assert len(data) in (128,1024)
 trailer=binascii.crc_hqx(data,0).to_bytes(2,'big') if crc else bytes([sum(data)&255])
 return bytes([1 if len(data)==128 else 2,number&255,(~number)&255])+data+trailer

def recipes():
 return [
  dict(name='empty',blocks=[]),
  dict(name='crc128',blocks=[payload(128)]),
  dict(name='crc1024',blocks=[payload(1024)]),
  dict(name='mixed128-1024-128',blocks=[payload(128),payload(1024,11),payload(128,99)]),
  dict(name='checksum128',blocks=[payload(128)],checksum=True),
  dict(name='checksum1024',blocks=[payload(1024)],checksum=True),
  dict(name='duplicate',blocks=[payload(128),payload(128,73)],duplicate=True),
  dict(name='badCRC-retry',blocks=[payload(128)],bad_crc=True),
  dict(name='bad-sequence-retry',blocks=[payload(128)],bad_sequence=True),
  dict(name='peer-doubleCAN',blocks=[],cancel='peer'),
  dict(name='local-Escape',blocks=[],cancel='escape'),
  dict(name='peer-doubleCAN-partial',blocks=[payload(128)],cancel='peer'),
  dict(name='local-Escape-partial',blocks=[payload(128)],cancel='escape'),
  dict(name='local-AltX',blocks=[],cancel='exit'),
  dict(name='existing-destination',blocks=[],existing=True),
  dict(name='SOFT-rejected',blocks=[],flow='SOFT',reject=True),
  dict(name='no-peer-timeout',blocks=[],silence=True),
 ]

class Peer:
 def __init__(self,recipe,*,negotiation_timeout=80,eot='nak-ack',destination=None):
  self.started=time.monotonic();self.recipe=recipe;self.negotiation_timeout=negotiation_timeout;self.eot=eot;self.destination=destination
  self.server=socket.socket();self.server.bind(('127.0.0.1',0));self.server.listen(1);self.server.settimeout(10)
  self.port=self.server.getsockname()[1];self.stop=threading.Event();self.wire=bytearray();self.pending=bytearray();self.sent=bytearray();self.events=[];self.errors=[];self.checks={};self.conn=None
  self.thread=threading.Thread(target=self.run,daemon=True)
 def log(self,event,**data):self.events.append(dict(event=event,seconds=round(time.monotonic()-self.started,3),**data))
 def send(self,data):
  self.conn.sendall(data);self.sent.extend(data)
 def receive(self):
  try:data=self.conn.recv(4096)
  except socket.timeout:return b''
  if not data:raise EOFError('DOS UART connection closed')
  self.wire.extend(data);self.pending.extend(data);return data
 def control(self,expected,timeout=12):
  deadline=time.monotonic()+timeout
  while time.monotonic()<deadline and not self.stop.is_set():
   while self.pending:
    value=self.pending.pop(0)
    if value in (6,0x15,0x18,ord('C'),ord('G')):
     self.log('DOS-control',value=value)
     if value not in expected:raise AssertionError(('Unexpected DOS control',value,expected))
     return value
   self.receive()
  raise TimeoutError('No expected DOS transfer control '+str(expected))
 def ready(self):
  deadline=time.monotonic()+5;next_probe=0
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_probe:self.send(b'\x1b[5n');next_probe=time.monotonic()+.25
   self.receive()
   if b'\x1b[0n' in self.pending:
    self.pending.clear();self.checks['actual_terminal_ready']=True;self.log('terminal-ready');return
  raise TimeoutError('Terminal never answered readiness DSR')
 def resume(self):
  deadline=time.monotonic()+10;next_probe=0;seen=bytearray()
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_probe:
    self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\x1b[5n');next_probe=time.monotonic()+.35
   data=self.receive();seen.extend(data)
   if b'\x1b[0n' in seen:self.checks['posttransfer_DSR']=True
   if b'ready' in seen.replace(b'\x1b[0n',b''):self.checks['posttransfer_keyboard']=True
   if self.checks.get('posttransfer_DSR') and self.checks.get('posttransfer_keyboard'):return
  raise TimeoutError('Posttransfer parser/keyboard did not resume')
 def run(self):
  r=self.recipe
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready()
    if r.get('existing') or r.get('reject'):
     # Give the local prompt/rejection time to run; incoming probes then verify
     # ordinary terminal ownership. No transfer control is expected or supplied.
     time.sleep(2.5);self.resume();self.checks['no_transfer_handshake']=b'C' not in self.wire and b'\x15' not in self.wire;return
    if r.get('silence'):
     self.control({ord('C')},self.negotiation_timeout);self.checks['actual_transfer_request']=True
     # Intentionally provide no transfer frames; main keys remain available.
     self.log('intentional-silence');time.sleep(r.get('silence_seconds',32));self.resume();return
    first=self.control({ord('C'),0x15},self.negotiation_timeout)
    if r.get('checksum'):
     while first!=0x15:first=self.control({ord('C'),0x15},self.negotiation_timeout)
    else:assert first==ord('C'),'Ordinary receive must start with CRC request'
    self.checks['negotiated_requested_integrity']=True
    if r.get('cancel'):
     for number,data in enumerate(r['blocks'],1):
      self.send(frame(data,number,not r.get('checksum')));self.control({6});self.log('partial-block-ACK',number=number)
     if r['cancel']=='peer':self.send(b'\x18\x18');self.log('sent-double-CAN')
     else:self.log('awaiting-real-BIOS-cancel',key=r['cancel'])
     if r['cancel']=='exit':
      while not self.stop.is_set():self.receive()
     else:time.sleep(.5 if r['cancel']=='peer' else 2);self.resume()
     return
    crc=not r.get('checksum')
    for number,data in enumerate(r['blocks'],1):
     valid=frame(data,number,crc)
     if r.get('bad_crc') and number==1:
      bad=bytearray(valid);bad[-1]^=1;self.send(bad);self.control({0x15});self.checks['bad_integrity_NAK']=True
     if r.get('bad_sequence') and number==1:
      self.send(frame(data,number+1,crc));self.control({0x15});self.checks['bad_sequence_NAK']=True
     self.send(valid);self.control({6});self.log('block-ACK',number=number,size=len(data))
     if r.get('duplicate') and number==1:
      self.send(valid);self.control({6});self.checks['duplicate_ACK']=True
    self.send(b'\x04');answer=self.control({6,0x15})
    if self.eot=='nak-ack':
     assert answer==0x15,'Expected initial EOT NAK';self.send(b'\x04');self.control({6})
    else:assert answer==6,'Expected single-EOT ACK'
    self.checks['complete_EOT_handshake']=True;self.log('final-ACK-observed')
    if self.destination is not None:
     self.checks['file_installed_before_final_ACK']=self.destination.exists() and self.destination.read_bytes()==b''.join(r['blocks'])
    self.resume()
  except EOFError:
   if r.get('cancel')=='exit':self.checks['actual_exit_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial close')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()

def key_recipe(recipe,*,filename='D:\\RECV.BIN',after_ms=6000):
 keys=['p1500','a-r']
 if not recipe.get('reject'):keys+=['p300']+list(filename)+['enter']
 if recipe.get('cancel')=='escape':keys+=['p1500','escape']
 elif recipe.get('cancel')=='exit':return ' '.join(keys+['p1500','a-x'])
 keys+=['p'+str(after_ms),'r','e','a','d','y','p1500','a-x']
 return ' '.join(keys)

def run_case(recipe,*,com=1,flow='HARD',negotiation_timeout=80,after_ms=None,dos_timeout=100,eot='nak-ack',label=None,expected_sha=None):
 if after_ms is None:after_ms=35000 if recipe.get('silence') else 17000 if recipe.get('checksum') else 6000
 name=recipe['name'];out=(OUT/label/name if label else OUT/name);out.mkdir(parents=True,exist_ok=True)
 # Only our fixed owned synthetic outputs are removed. Unexpected files remain
 # visible and fail the cleanup assertion rather than being silently discarded.
 for name2 in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','RECV.BIN'):(out/name2).unlink(missing_ok=True)
 if recipe.get('existing'):(out/'RECV.BIN').write_bytes(b'OWNED EXISTING DESTINATION')
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[com-1]
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 peer=Peer(recipe,negotiation_timeout=negotiation_timeout,eot=eot,destination=out/'RECV.BIN');peer.thread.start()
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==com else 'disabled') for i in range(1,5))
 args='COM'+str(com)+' 38400 8N1 '+recipe.get('flow',flow)
 keys=key_recipe(recipe,after_ms=after_ms)
 config=f'''[sdl]
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
ADDKEY {keys}
TERMINAL {args}
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto capture
:fail
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
 (out/'dosbox.conf').write_text(config);digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();start=time.monotonic()
 assert expected_sha is None or digest==expected_sha,'Terminal changed between cases'
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=dos_timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set();peer.server.close();peer.thread.join(1)
 before=(out/'BEFORE.BIN').read_bytes() if (out/'BEFORE.BIN').exists() else b''
 after=(out/'AFTER.BIN').read_bytes() if (out/'AFTER.BIN').exists() else b''
 screen=(out/'SCREEN.BIN').read_bytes() if (out/'SCREEN.BIN').exists() else b''
 target=out/'RECV.BIN';expected=b''.join(recipe['blocks'])
 success=not any(recipe.get(k) for k in ('cancel','existing','reject','silence'))
 checks=dict(peer.checks)
 checks['required_terminal_ready']=bool(checks.get('actual_terminal_ready'))
 if success or recipe.get('cancel'):
  checks['required_actual_negotiation']=bool(checks.get('negotiated_requested_integrity'))
 if success:
  checks['required_final_ACK']=bool(checks.get('complete_EOT_handshake'))
  checks['required_install_before_ACK']=bool(checks.get('file_installed_before_final_ACK'))
 if recipe.get('cancel')=='exit':checks['required_serial_close']=bool(checks.get('actual_exit_closed_serial'))
 else:
  checks['required_posttransfer_DSR']=bool(checks.get('posttransfer_DSR'))
  checks['required_posttransfer_keyboard']=bool(checks.get('posttransfer_keyboard'))
 if recipe.get('silence'):checks['required_actual_request']=bool(checks.get('actual_transfer_request'))
 checks.update(DOS_expected_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,no_peer_errors=not peer.errors,binary_unchanged=digest==hashlib.sha256(BINARY.read_bytes()).hexdigest())
 if success:checks['exact_received_file']=target.exists() and target.read_bytes()==expected
 elif recipe.get('existing'):checks['existing_destination_unchanged']=target.read_bytes()==b'OWNED EXISTING DESTINATION'
 else:checks['failed_transfer_not_installed']=not target.exists()
 if recipe.get('cancel')!='exit':checks['posttransfer_screen']=len(screen)==4000 and screen[:28:2]==b'AFTER TRANSFER'
 allowed={'sampler.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','RECV.BIN','serial.bin','peer.bin','events.json','result.json','screen.txt'}
 checks['no_leftover_stage_files']=not [p.name for p in out.iterdir() if p.name not in allowed]
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent)
 (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 (out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(case=recipe['name'],passed=all(checks.values()),checks=checks,errors=peer.errors,binary_sha256=digest,command=args,keys=keys,seconds=round(time.monotonic()-start,3),scope='Actual source-built DOS terminal, BIOS AltR/UI, native receive engine, real UART/IRQ and DOS files. Independent loopback peer supplies no terminal-generated responses. Synthetic media only; no physical modem/timing claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(recipe['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--case',action='append',default=[]);parser.add_argument('--label',help='Separate owned artifact folder for independent reruns');parser.add_argument('--sha256',required=True,help='Explicit frozen terminal hash; mismatches refuse execution');parser.add_argument('--com',type=int,choices=range(1,5),default=1);parser.add_argument('--flow',choices=['HARD','NONE'],default='HARD');parser.add_argument('--after-ms',type=int,default=None);parser.add_argument('--dos-timeout',type=int,default=100);parser.add_argument('--negotiation-timeout',type=int,default=80);parser.add_argument('--eot',choices=['nak-ack','ack'],default='nak-ack');a=parser.parse_args()
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Terminal does not match explicit freeze'
 if a.label:assert a.label.replace('-','').replace('_','').isalnum(),'Invalid owned artifact label'
 selected=[r for r in recipes() if not a.case or r['name'] in a.case];assert selected,'No matching cases'
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  results=[run_case(r,com=a.com,flow=a.flow,negotiation_timeout=a.negotiation_timeout,after_ms=a.after_ms,dos_timeout=a.dos_timeout,eot=a.eot,label=a.label,expected_sha=a.sha256) for r in selected]
 summary=dict(passed=all(r['passed'] for r in results),binary_sha256=a.sha256,cases=results);summary_path=(OUT/a.label if a.label else OUT);summary_path.mkdir(parents=True,exist_ok=True);(summary_path/'checks.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
