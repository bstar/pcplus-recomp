#!/usr/bin/env python3
"""Independent actual-DOS Alt-S upload peer on synthetic, owned test media.

Requires an explicit runtime freeze. No drive/original/private config is opened.
The peer independently validates framing/integrity/sequence/padding and never
supplies a response which the terminal itself is supposed to generate.
"""
import argparse,binascii,fcntl,hashlib,json,math,os,socket,subprocess,time
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as TerminalPeer
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';OUT=ROOT/'build/terminal-upload-dos'

def payload(count,seed=0):return bytes((i*37+seed)%256 for i in range(count))
def expected_blocks(data):
 """Native protocol2: initial1K, tail switches only below897 remaining."""
 size=1024 if len(data)>=1024 else 128;position=0;out=[]
 while position<len(data):
  out.append(data[position:position+size].ljust(size,b'\x1a'));position+=size
  if len(data)-position<897:size=128
 return out

def recipes():
 return [
  dict(name='empty',data=b''),dict(name='partial-binary',data=payload(117)+b'\x1a\x00\xff\x11\x13\x1a'),
  dict(name='crc128',data=payload(128)),dict(name='crc1024',data=payload(1024)),
  dict(name='tail896',data=payload(1920)),dict(name='tail897',data=payload(1921)),
  dict(name='checksum128',data=payload(128),checksum=True),dict(name='checksum1024',data=payload(1024),checksum=True),
  dict(name='mixed-over10K',data=payload(11521)),dict(name='over64K',data=payload(70001)),
  dict(name='block-rollover',data=payload(263169),large=True),
  dict(name='NAK-retry',data=payload(128),nak=True),dict(name='dropped-ACK',data=payload(128),drop_ack=True),
  dict(name='peer-CAN',data=payload(128),cancel='peer'),dict(name='peer-CAN-over10K',data=payload(11521),cancel='peer'),dict(name='local-Escape',data=payload(128),cancel='escape'),
  dict(name='local-AltX',data=payload(128),cancel='exit'),
  dict(name='missing-source',data=None,filename='D:\\MISSING.BIN',reject=True,prompt=True),
  dict(name='device-source',data=None,filename='NUL',reject=True,prompt=True),
  dict(name='invalid-path',data=None,filename='D:\\BAD?.BIN',reject=True,prompt=True),
  dict(name='directory-source',data=None,filename='D:\\SUBDIR',directory=True,reject=True,prompt=True),
  dict(name='SOFT-rejected',data=payload(128),flow='SOFT',reject=True),
 ]

class UploadPeer(TerminalPeer):
 def __init__(self,recipe,*,packet_timeout=15):
  self.packet_timeout=packet_timeout;self.frames=[];self.accepted=[];self.eots=0
  super().__init__(recipe)
 def exact(self,count,timeout=None):
  deadline=time.monotonic()+(timeout or self.packet_timeout)
  while len(self.pending)<count and time.monotonic()<deadline and not self.stop.is_set():self.receive()
  if len(self.pending)<count:raise TimeoutError('Incomplete upload packet: '+str((count,len(self.pending))))
  result=bytes(self.pending[:count]);del self.pending[:count];return result
 def packet(self):
  lead=self.exact(1)[0]
  if lead in (4,0x18):return lead,None
  if lead not in (1,2):raise AssertionError(('Unexpected upload packet leader',lead))
  size=128 if lead==1 else 1024;crc=not self.recipe.get('checksum');rest=self.exact(2+size+(2 if crc else 1))
  number,complement=rest[:2];data=rest[2:2+size];trailer=rest[2+size:]
  assert number^complement==255,'Upload block complement mismatch'
  correct=binascii.crc_hqx(data,0).to_bytes(2,'big') if crc else bytes([sum(data)&255])
  assert trailer==correct,'Upload CRC/checksum mismatch'
  result=dict(number=number,size=size,payload=data.hex(),packet_sha256=hashlib.sha256(bytes([lead])+rest).hexdigest())
  self.frames.append(result);self.log('validated-frame',number=number,size=size,sha256=result['packet_sha256']);return lead,result
 def negotiate(self):
  # Real AltS/prompt occurs at~1.5s/1.8s from DOS startup. Repeat only until
  # the first packet leader; never inject negotiation into a payload packet.
  time.sleep(1.9);deadline=time.monotonic()+10;next_send=0
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_send:
    self.send(b'\x15' if self.recipe.get('checksum') else b'C');next_send=time.monotonic()+.5
   self.receive()
   if self.pending:
    self.checks['actual_upload_started']=self.pending[0] in (1,2,4)
    return
  raise TimeoutError('DOS never started upload after negotiation')
 def cancelled(self):
  # A first frame was validated but intentionally not ACKed. Wait for the
  # actual runtime's best-effort CANpair, not a scripted product response.
  deadline=time.monotonic()+6;tail=bytearray()
  while time.monotonic()<deadline and not self.stop.is_set():
   if self.pending:tail.extend(self.pending);self.pending.clear()
   if b'\x18\x18' in tail:
    self.checks['actual_cancel_CAN_pair']=True
    self.checks['no_EOT_after_cancel']=b'\x04' not in tail;return
   self.receive()
  raise TimeoutError('Upload cancellation did not emit CANpair')
 def resume(self):
  # Large-file tests schedule real BIOS keys conservatively; a fast emulator
  # may finish serial transfer sooner than physical baud arithmetic predicts.
  deadline=time.monotonic()+getattr(self,'resume_timeout',10);next_probe=0;seen=bytearray()
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_probe:
    self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\x1b[5n');next_probe=time.monotonic()+.35
   seen.extend(self.receive())
   if b'\x1b[0n' in seen:self.checks['posttransfer_DSR']=True
   if b'ready' in seen.replace(b'\x1b[0n',b''):self.checks['posttransfer_keyboard']=True
   if self.checks.get('posttransfer_DSR') and self.checks.get('posttransfer_keyboard'):return
  raise TimeoutError('Postupload parser/keyboard did not resume')
 def run(self):
  r=self.recipe
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready()
    if r.get('reject'):
     time.sleep(2.5)
     # Actively offer negotiation: silent peers cannot prove that NUL or an
     # invalid source was rejected rather than waiting inside the sender.
     self.send(b'C');time.sleep(.3);self.receive();self.resume()
     self.checks['no_upload_frame']=not any(c in self.wire for c in (1,2,4));return
    self.negotiate();blocks=expected_blocks(r['data'])
    if r.get('cancel'):
     lead,got=self.packet();assert lead in (1,2) and bytes.fromhex(got['payload'])==blocks[0]
     self.checks['actual_partial_frame_validated']=True
     if r['cancel']=='peer':self.send(b'\x18\x18');self.log('peer-sent-double-CAN')
     else:self.log('awaiting-BIOS-cancel',key=r['cancel'])
     self.cancelled()
     if r['cancel']=='exit':
      while not self.stop.is_set():self.receive()
     else:self.resume()
     return
    for index,expected in enumerate(blocks):
     lead,got=self.packet();assert lead in (1,2) and got['number']==(index+1)&255
     assert bytes.fromhex(got['payload'])==expected,('Wrong source/padding/size',index,got['size'],len(expected))
     if index==0 and (r.get('nak') or r.get('drop_ack')):
      if r.get('nak'):self.send(b'\x15');self.log('peer-NAK-first-frame')
      else:self.log('peer-dropped-first-ACK')
      _,retry=self.packet();assert retry==got,'Retry changed frame bytes or sequence'
      self.checks['identical_retransmission']=True
     self.send(b'\x06');self.accepted.append(got);self.log('peer-ACK',number=got['number'])
    lead,packet=self.packet();assert lead==4,'Missing EOT after complete source';self.eots+=1
    self.send(b'\x15');self.log('peer-NAK-first-EOT')
    lead,packet=self.packet();assert lead==4,'Native sender did not repeat EOT';self.eots+=1
    self.send(b'\x06');self.log('peer-ACK-second-EOT')
    self.checks['EOT_NAK_then_ACK']=True
    sent=b''.join(bytes.fromhex(f['payload']) for f in self.accepted)
    self.checks['exact_source_and_padding']=sent[:len(r['data'])]==r['data'] and sent[len(r['data']):]==b'\x1a'*(len(sent)-len(r['data']))
    self.checks['expected_block_count']=len(self.accepted)==len(blocks)
    if len(blocks)>255:self.checks['block_sequence_rolled_over']=self.accepted[255]['number']==0 and self.accepted[256]['number']==1
    self.resume()
  except EOFError:
   if r.get('cancel')=='exit':self.checks['actual_exit_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial close')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()

def keys_for(r,after_ms):
 keys=['p1500','a-s']
 if not r.get('reject') or r.get('prompt'):keys+=['p300']+list(r.get('filename','D:\\SEND.BIN'))+['enter']
 if r.get('cancel')=='escape':keys+=['p1500','escape']
 if r.get('cancel')=='exit':return ' '.join(keys+['p1500','a-x'])
 return ' '.join(keys+['p'+str(after_ms),'r','e','a','d','y','p1500','a-x'])

def run_case(r,*,sha,label,com=1,flow='HARD',after_ms=None,dos_timeout=None):
 out=OUT/label/r['name'];out.mkdir(parents=True,exist_ok=True)
 assert not (out/'result.json').exists(),'Use a fresh label to retain previous artifacts'
 data=r.get('data');source=out/'SEND.BIN'
 if data is not None:source.write_bytes(data)
 if r.get('directory'):(out/'SUBDIR').mkdir(exist_ok=True)
 before_source=source.stat() if source.exists() else None
 if after_ms is None:
  after_ms=max(6000,math.ceil((len(data or b'')*10/38400+4)*1000))
  if r.get('drop_ack'):after_ms+=12000
 if dos_timeout is None:dos_timeout=max(35,math.ceil(after_ms/1000)+20)
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[com-1]
 for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(base+off))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 peer=UploadPeer(r);peer.resume_timeout=max(10,after_ms/1000+4);peer.thread.start()
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==com else 'disabled') for i in range(1,5))
 args='COM'+str(com)+' 38400 8N1 '+r.get('flow',flow);keys=keys_for(r,after_ms)
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
 (out/'dosbox.conf').write_text(config);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha,'Runtime changed before case'
 started=time.monotonic()
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=dos_timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set();peer.server.close();peer.thread.join(1)
 before=(out/'BEFORE.BIN').read_bytes() if (out/'BEFORE.BIN').exists() else b'';after=(out/'AFTER.BIN').read_bytes() if (out/'AFTER.BIN').exists() else b'';screen=(out/'SCREEN.BIN').read_bytes() if (out/'SCREEN.BIN').exists() else b''
 checks=dict(peer.checks);checks.update(DOS_expected_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,no_peer_errors=not peer.errors,binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==sha,actual_ready=bool(peer.checks.get('actual_terminal_ready')))
 if data is not None:
  st=source.stat() if source.exists() else None;checks['source_bytes_unchanged']=source.exists() and source.read_bytes()==data
  checks['source_metadata_unchanged']=st is not None and (st.st_ino,st.st_size,st.st_mtime_ns)==(before_source.st_ino,before_source.st_size,before_source.st_mtime_ns)
 else:checks['missing_source_not_created']=not source.exists()
 if r.get('reject'):checks['required_no_upload_frame']=bool(checks.get('no_upload_frame'))
 elif r.get('cancel'):
  checks['required_started']=bool(checks.get('actual_upload_started'));checks['required_valid_partial_frame']=bool(checks.get('actual_partial_frame_validated'));checks['required_CAN_pair']=bool(checks.get('actual_cancel_CAN_pair'));checks['required_no_EOT']=bool(checks.get('no_EOT_after_cancel'))
 else:
  checks['required_started']=bool(checks.get('actual_upload_started'));checks['required_complete_EOT']=bool(checks.get('EOT_NAK_then_ACK'));checks['required_exact_source']=bool(checks.get('exact_source_and_padding'));checks['required_count']=bool(checks.get('expected_block_count'))
 if r.get('cancel')=='exit':checks['required_actual_exit']=bool(checks.get('actual_exit_closed_serial'))
 else:
  checks['required_resume_DSR']=bool(checks.get('posttransfer_DSR'));checks['required_resume_keyboard']=bool(checks.get('posttransfer_keyboard'));checks['posttransfer_screen']=len(screen)==4000 and screen[:28:2]==b'AFTER TRANSFER'
 allowed={'SEND.BIN','SUBDIR','sampler.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','serial.bin','peer.bin','events.json','frames.json','result.json','screen.txt'}
 if r.get('directory'):checks['directory_source_untouched']=not list((out/'SUBDIR').iterdir())
 checks['no_other_files_created']=not [p.name for p in out.iterdir() if p.name not in allowed]
 (out/'serial.bin').write_bytes(peer.wire);(out/'peer.bin').write_bytes(peer.sent);(out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'frames.json').write_text(json.dumps(peer.frames,indent=2)+'\n');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(case=r['name'],passed=all(checks.values()),checks=checks,errors=peer.errors,binary_sha256=sha,command=args,keys=keys,source_size=len(data) if data is not None else None,source_sha256=hashlib.sha256(data).hexdigest() if data is not None else None,validated_frames=len(peer.frames),accepted_blocks=len(peer.accepted),eots=peer.eots,seconds=round(time.monotonic()-started,3),scope='Actual DOS AltS/native sender, independent binaryframe peer, unchanged ownedsource, real UART/IRQ/files and hardware/parser/keyboard resume. Loopback model, not physicalCTS/DCD or cable timing.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);p.add_argument('--large',action='store_true',help='Include optional263169byte block-number rollover');p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--after-ms',type=int);p.add_argument('--dos-timeout',type=int);a=p.parse_args()
 assert a.label.replace('-','').replace('_','').isalnum(),'Invalid owned artifact label';assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime does not match requested freeze'
 selected=[r for r in recipes() if (r['name'] in a.case if a.case else (a.large or not r.get('large')))];assert selected,'No selected scenarios';OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);rows=[run_case(r,sha=a.sha256,label=a.label,com=a.com,flow=a.flow,after_ms=a.after_ms,dos_timeout=a.dos_timeout) for r in selected]
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
