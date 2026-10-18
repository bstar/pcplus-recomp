#!/usr/bin/env python3
"""Independent actualDOS YMODEM peer on fresh, owned synthetic media.

No application reply or product callback is mocked: DOS uses real BIOS hotkeys,
UART/IRQ, filesystem and maintained engine. Peer supplies only remote protocol,
terminal queries and application banner. Explicit frozen runtime hash required.
"""
import argparse,fcntl,hashlib,json,os,re,socket,subprocess,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as TerminalPeer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-ymodem-dos';BINARY=ROOT/'build/terminal/TERMINAL.EXE'
def payload(n,seed=0):return bytes((i*37+seed)&255 for i in range(n))
def crc16(data):
 crc=0
 for byte in data:
  crc^=byte<<8
  for _ in range(8):crc=((crc<<1)^0x1021 if crc&0x8000 else crc<<1)&65535
 return crc
def frame(data,number):
 assert len(data) in (128,1024)
 return bytes([1 if len(data)==128 else 2,number&255,(~number)&255])+data+crc16(data).to_bytes(2,'big')
def header(name=b'',size=None,capacity=128,metadata=None):
 raw=name+b'\0'
 if name:raw+=(str(size).encode() if size is not None else b'') if metadata is None else metadata
 assert len(raw)<capacity;return raw.ljust(capacity,b'\0')
def file(name,data,*,known=True,sizes=None):return dict(name=name,data=data,known=known,sizes=sizes)
def recipes():
 single=[file('ONE.BIN',payload(117)+b'\x1a\x00\xff\x11\x13')]
 multi=[file('EMPTY.BIN',b''),file('ONE.BIN',payload(117)+b'\x1a\x00\xff\x11\x13'),file('BIG.BIN',payload(2501,73),sizes=[128,1024,1024,1024])]
 return [dict(name='rx-empty-batch',direction='rx',files=[]),dict(name='rx-zero-size',direction='rx',files=[file('ZERO.BIN',b'')]),dict(name='rx-binary',direction='rx',files=single),dict(name='rx-grace-SOH-prefix-single-DSR',direction='rx',files=single,grace_prefix=b'\x01ABC'),dict(name='rx-grace-STX-prefix-single-DSR',direction='rx',files=single,grace_prefix=b'\x02ABC'),dict(name='rx-multi-mixed',direction='rx',files=multi),dict(name='rx-unknown-size',direction='rx',files=[file('UNKNOWN.BIN',payload(123),known=False)]),dict(name='rx-sequence-rollover',direction='rx',files=[file('ROLL.BIN',payload(128*257+1))]),dict(name='rx-known-length-extra-frame',direction='rx',files=single,extra_frame=True),dict(name='rx-short-EOT',direction='rx',files=[file('SHORT.BIN',payload(129))],short_eot=True),dict(name='rx-header1024',direction='rx',files=single,header_capacity=1024),dict(name='rx-bad-header-CRC',direction='rx',files=single,bad_header=True),dict(name='rx-duplicate-header',direction='rx',files=single,duplicate_header=True),dict(name='rx-bad-data-CRC',direction='rx',files=single,bad_data=True),dict(name='rx-duplicate-data',direction='rx',files=single,duplicate_data=True),dict(name='rx-lost-final-header-ACK',direction='rx',files=single,end_retry=True),dict(name='rx-existing-destination',direction='rx',files=single,conflict=True),dict(name='rx-partial-batch-bad-next-header',direction='rx',files=single,partial_bad_header=True),dict(name='rx-unsafe-path',direction='rx',files=[file('../BAD.BIN',b'')],reject=True),dict(name='rx-peer-CAN',direction='rx',files=single,cancel='peer'),dict(name='rx-local-Escape',direction='rx',files=single,cancel='escape'),dict(name='rx-local-AltX',direction='rx',files=single,cancel='exit'),dict(name='tx-empty-pattern',direction='tx',files=[]),dict(name='tx-zero-size',direction='tx',files=[file('ZERO.BIN',b'')]),dict(name='tx-binary',direction='tx',files=single),dict(name='tx-multi',direction='tx',files=multi),dict(name='tx-NAK-data-retry',direction='tx',files=single,data_nak=True),dict(name='tx-lost-header-ACK',direction='tx',files=single,header_retry=True),dict(name='tx-final-ACK-missing-application',direction='tx',files=single,end_unconfirmed=True),dict(name='tx-lost-final-header-ACK',direction='tx',files=single,end_retry=True)]

def blocks(item):
 data=item['data'];sizes=list(item.get('sizes') or []);out=[];at=0
 while at<len(data):
  size=sizes.pop(0) if sizes else 128;part=data[at:at+size].ljust(size,b'\x1a');out.append(part);at+=size
 return out
class BatchPeer(TerminalPeer):
 def __init__(self,recipe,destination):
  self.destination_dir=destination;self.frames=[];self.completed={};self.headers=[];self.resume_timeout=25
  super().__init__(recipe)
 def exact(self,count,timeout=13):
  deadline=time.monotonic()+timeout
  while len(self.pending)<count and time.monotonic()<deadline and not self.stop.is_set():self.receive()
  if len(self.pending)<count:raise TimeoutError(('Incomplete YMODEM packet',count,len(self.pending)))
  raw=bytes(self.pending[:count]);del self.pending[:count];return raw
 def packet(self):
  lead=self.exact(1)[0]
  if lead in (4,24):return lead,None
  assert lead in (1,2),('Unexpected YMODEM leader',lead)
  size=128 if lead==1 else 1024;rest=self.exact(size+4);number,complement=rest[:2];data=rest[2:-2]
  assert number^complement==255,'Bad sequence complement';assert crc16(data)==int.from_bytes(rest[-2:],'big'),'Bad actualDOS frame CRC'
  self.frames.append(dict(number=number,size=size,sha256=hashlib.sha256(bytes([lead])+rest).hexdigest()))
  self.log('actualDOS-frame',number=number,size=size);return number,data
 def cancel_pair(self):self.control({24});self.control({24});self.checks['actual_CAN_pair']=True
 def resume(self):
  # Transfer completion may precede scheduled real BIOS keys by many seconds.
  # Preserve DSR, keyboard and video requirements with a bounded recipe-aware wait.
  deadline=time.monotonic()+self.resume_timeout;next_probe=0;seen=bytearray()
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_probe:
    self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\x1b[5n');next_probe=time.monotonic()+.35
   seen.extend(self.receive())
   if b'\x1b[0n' in seen:self.checks['posttransfer_DSR']=True
   if b'ready' in seen.replace(b'\x1b[0n',b''):self.checks['posttransfer_keyboard']=True
   if self.checks.get('posttransfer_DSR') and self.checks.get('posttransfer_keyboard'):return
  raise TimeoutError('YMODEM posttransfer parser/keyboard did not resume within recipe bound')
 def resume_prefix(self,prefix,delay=1.2):
  # Deliberately resemble a truncated frame during end-header lost-ACK grace.
  # One delayed application probe must survive: repeating it would conceal loss.
  start=len(self.sent);self.send(prefix);self.log('application-prefix-during-grace',hex=prefix.hex())
  if delay:time.sleep(delay)
  self.send(b'\x1b[2J\x1b[HAFTER TRANSFER\x1b[5n');self.log('single-application-banner-DSR')
  deadline=time.monotonic()+self.resume_timeout;seen=bytearray()
  while time.monotonic()<deadline and not self.stop.is_set():
   seen.extend(self.receive())
   if b'\x1b[0n' in seen:self.checks['posttransfer_DSR']=True
   if b'ready' in seen.replace(b'\x1b[0n',b''):self.checks['posttransfer_keyboard']=True
   if self.checks.get('posttransfer_DSR') and self.checks.get('posttransfer_keyboard'):
    self.checks['single_posttransfer_probe']=bytes(self.sent[start:]).count(b'\x1b[5n')==1
    self.checks['single_actual_DSR_response']=seen.count(b'\x1b[0n')==1
    return
  raise TimeoutError('Single post-grace application DSR/keyboard lost after '+prefix.hex())
 def rx(self):
  r=self.recipe;self.control({67},20);self.checks['actual_CRC_request']=True
  if r.get('cancel'):
   if r['cancel']=='peer':self.send(b'\x18\x18')
   else:self.log('awaiting-real-BIOS-cancel',key=r['cancel'])
   if r['cancel']=='exit':
    while not self.stop.is_set():self.receive()
   else:
    self.cancel_pair();self.resume()
   return
  for index,item in enumerate(r['files']):
   name=item['name'].encode('ascii');h=frame(header(name,len(item['data']) if item['known'] else None,r.get('header_capacity',128)),0)
   if r.get('bad_header') and index==0:
    bad=bytearray(h);bad[-1]^=1;self.send(bad);self.control({21});self.checks['bad_header_NAK']=True
   self.send(h)
   if r.get('conflict') or r.get('reject'):self.cancel_pair();self.resume();return
   self.control({6});self.control({67});self.headers.append(item['name'])
   if r.get('duplicate_header') and index==0:
    self.send(h);self.control({6});self.control({67});self.checks['duplicate_header_ACK_C']=True
   parts=blocks(item)
   if r.get('short_eot'):parts=parts[:1]
   for seq,body in enumerate(parts,1):
    packet=frame(body,seq)
    if r.get('bad_data') and seq==1:
     bad=bytearray(packet);bad[-1]^=1;self.send(bad);self.control({21});self.checks['bad_data_NAK']=True
    self.send(packet);self.control({6})
    if r.get('duplicate_data') and seq==1:self.send(packet);self.control({6});self.checks['duplicate_data_ACK']=True
   if r.get('extra_frame'):
    self.send(frame(payload(128,99),len(parts)+1));self.cancel_pair();self.checks['distinct_extra_frame_rejected']=True;self.resume();return
   if r.get('short_eot'):
    self.send(b'\x04');answer=self.control({21,24})
    if answer==21:self.send(b'\x04');self.cancel_pair()
    else:self.control({24});self.checks['actual_CAN_pair']=True
    self.checks['short_EOT_rejected_without_ACK']=True;self.resume();return
   self.send(b'\x04');self.control({21});self.send(b'\x04');self.control({6})
   expected=item['data'] if item['known'] else b''.join(parts)
   target=self.destination_dir/item['name'];assert target.exists() and target.read_bytes()==expected,('File not exact/installed before EOT ACK',item['name'])
   self.completed[item['name']]=hashlib.sha256(expected).hexdigest();self.control({67})
  if r.get('partial_bad_header'):
   self.send(frame(header(b'../BAD.BIN',0),0));self.cancel_pair()
   self.checks['earlier_committed_file_survived']=all((self.destination_dir/i['name']).read_bytes()==i['data'] for i in r['files'])
   self.resume();return
  end=frame(bytes(128),0);self.send(end);self.control({6})
  if r.get('end_retry'):time.sleep(.4);self.send(end);self.control({6});self.checks['repeated_end_header_ACK']=True
  self.checks['batch_end_ACK']=True;self.checks['exact_files_before_EOT_ACK']=True
  # First actual application byte must be rewound out of lost-ACK grace.
  self.resume_prefix(r['grace_prefix']) if r.get('grace_prefix') else self.resume()
 def tx(self):
  r=self.recipe;time.sleep(2.2);self.send(b'C');expected={i['name'].upper():i['data'] for i in r['files']};seen=set()
  while True:
   seq,h=self.packet();assert seq==0 and h is not None,'Expected block0 header'
   end=h.find(b'\0');assert end>=0,'Unterminated actualDOS metadata name'
   if not end:
    assert not any(h),'Nonzero end-header tail'
    if r.get('end_unconfirmed'):
     # A real remote application resumed without confirming final empty header.
     # Never manufacture its ACK: require terminal response to one application
     # query, and reject any retransmitted frame/CAN in the response interval.
     start=len(self.wire)-len(self.pending)
     self.checks['final_header_deliberately_unACKed']=True
     self.resume_prefix(b'',delay=0)
     after=bytes(self.wire[start:])
     self.checks['no_frame_or_CAN_after_unconfirmed_end']=not any(c in after for c in (1,2,24))
     assert seen==set(expected),'Missing source files before unconfirmed end'
     self.checks['exact_all_source_files']=True
     return
    if r.get('end_retry'):
     seq,retry=self.packet();assert seq==0 and retry==h,'Changed final-header retransmission';self.checks['final_header_retry_identical']=True
    self.send(b'\x06');break
   name=h[:end].decode('ascii').upper();assert name in expected and name not in seen,('Unknown/duplicate batch source',name)
   meta=h[end+1:].split(b'\0',1)[0].split(b' ');assert re.fullmatch(b'[0-9]+',meta[0]);size=int(meta[0]);assert size==len(expected[name]),'Wrong source DWORD size'
   self.headers.append(name)
   if r.get('header_retry') and not seen:
    seq,retry=self.packet();assert seq==0 and retry==h,'Changed header retransmission';self.checks['header_retry_identical']=True
   self.send(b'\x06C');number=1;content=bytearray();previous=None
   while True:
    seq,data=self.packet()
    if data is None:
     assert seq==4,'Unexpected cancellation';self.send(b'\x15');seq,data=self.packet();assert seq==4 and data is None,'Missing second EOT';self.send(b'\x06C');break
    assert seq==number&255,('Unexpected upload data number',seq,number)
    if r.get('data_nak') and number==1:
     self.send(b'\x15');retry_seq,retry=self.packet();assert retry_seq==seq and retry==data,'Changed data retry';self.checks['data_retry_identical']=True
    content.extend(data);self.send(b'\x06');number+=1;previous=data
   assert content[:size]==expected[name] and content[size:]==b'\x1a'*(len(content)-size),'ActualDOS upload source/padding differs'
   seen.add(name);self.completed[name]=hashlib.sha256(content[:size]).hexdigest()
  assert seen==set(expected),'Missing files from actual batch';self.checks['exact_all_source_files']=True;self.checks['batch_end_ACK']=True;self.resume()
 def run(self):
  try:
   conn,_=self.server.accept();self.conn=conn
   with conn:
    conn.settimeout(.1);self.ready();self.rx() if self.recipe['direction']=='rx' else self.tx()
  except EOFError:
   if self.recipe.get('cancel')=='exit':self.checks['actual_exit_closed_serial']=True
   elif not self.stop.is_set():self.errors.append('Unexpected serial EOF')
  except Exception as error:
   if not self.stop.is_set():self.errors.append(str(error))
  finally:self.server.close()

def run_case(r,a):
 out=OUT/a.label/r['name'];out.mkdir(parents=True,exist_ok=False);(out/'RECV').mkdir();(out/'SEND').mkdir()
 source_meta={}
 if r['direction']=='tx':
  for item in r['files']:
   p=out/'SEND'/item['name'];p.write_bytes(item['data']);st=p.stat();source_meta[p.name]=(st.st_ino,st.st_size,st.st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest())
 if r.get('conflict'):(out/'RECV'/r['files'][0]['name']).write_bytes(b'OWNED EXISTING')
 sampler=SAMPLER;base=(0x3f8,0x2f8,0x3e8,0x2e8)[a.com-1]
 for offset in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+offset),hex(base+offset))
 (out/'sampler.asm').write_text(sampler);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 peer=BatchPeer(r,out/'RECV');peer.resume_timeout=min(130,max(10,a.after_ms/1000+10));peer.thread.start();filename='D:\\RECV\\' if r['direction']=='rx' else 'D:\\SEND\\*.BIN'
 keys=['p1500','a-r' if r['direction']=='rx' else 'a-s','p300','f2','p300']+list(filename)+['enter']
 if r.get('cancel') in ('escape','exit'):keys+=['p2000','escape' if r['cancel']=='escape' else 'a-x']
 else:keys+=['p'+str(a.after_ms),'r','e','a','d','y','p1500','a-x']
 if r.get('cancel')=='escape':keys+=['p2000','r','e','a','d','y','p1500','a-x']
 serial='\n'.join('serial'+str(i)+'='+(f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 rxdelay:200 txdelay:1' if i==a.com else 'disabled') for i in range(1,5))
 command=f'C:\\TERMINAL COM{a.com} {a.baud} 8N1 {a.flow}'
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[serial]\n{serial}\n[autoexec]\n@echo off\nmount c "{BINARY.parent}"\nmount d "{out}"\nd:\nSNAP B\nADDKEY {' '.join(keys)}\n{command}\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto capture\n:fail\necho FAIL>FAIL.TXT\n:capture\nSNAP S\nSNAP A\nexit\n'''
 (out/'dosbox.conf').write_text(config);assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Runtime changed before launch';started=time.monotonic()
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=a.timeout).returncode
  except subprocess.TimeoutExpired:code=-1
 peer.stop.set()
 if peer.conn:
  try:peer.conn.shutdown(socket.SHUT_RDWR)
  except OSError:pass
 peer.server.close();peer.thread.join(2)
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 before,after,screen=read('BEFORE.BIN'),read('AFTER.BIN'),read('SCREEN.BIN');checks=dict(peer.checks)
 checks.update(actual_terminal_ready=bool(checks.get('actual_terminal_ready')),DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),hardware_restored=len(before)==42 and before==after,no_peer_errors=not peer.errors,binary_unchanged=hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256)
 failed=any(r.get(k) for k in ('conflict','reject','cancel','extra_frame','short_eot','partial_bad_header'))
 if not failed:
  checks['required_final_end_policy']=bool(checks.get('final_header_deliberately_unACKed') and checks.get('no_frame_or_CAN_after_unconfirmed_end')) if r.get('end_unconfirmed') else bool(checks.get('batch_end_ACK'))
  checks['required_exact_transfer']=bool(checks.get('exact_files_before_EOT_ACK') if r['direction']=='rx' else checks.get('exact_all_source_files'))
 else:checks['required_actual_CRC_request']=bool(checks.get('actual_CRC_request'))
 if r.get('cancel')=='exit':checks['required_exit_closed_serial']=bool(checks.get('actual_exit_closed_serial'))
 else:checks.update(required_resume_DSR=bool(checks.get('posttransfer_DSR')),required_resume_keyboard=bool(checks.get('posttransfer_keyboard')),posttransfer_screen=len(screen)==4000 and screen[:28:2]==b'AFTER TRANSFER')
 if r['direction']=='rx':
  expected={} if failed else {i['name']:(i['data'] if i['known'] else b''.join(blocks(i))) for i in r['files']}
  if r.get('partial_bad_header'):expected={i['name']:i['data'] for i in r['files']}
  if r.get('conflict'):expected[r['files'][0]['name']]=b'OWNED EXISTING'
  checks['exact_destination_tree']={p.name:p.read_bytes() for p in (out/'RECV').iterdir() if p.is_file()}==expected
 else:
  checks['all_source_content_and_metadata_unchanged']={p.name for p in (out/'SEND').iterdir()}==set(source_meta) and all((p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest())==source_meta[p.name] for p in (out/'SEND').iterdir())
 allowed={'sampler.asm','SNAP.COM','dosbox.conf','dosbox.log','PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'}
 checks['no_unexpected_root_files']=not [p for p in out.iterdir() if p.name not in allowed|{'RECV','SEND'}]
 checks['no_staging_or_other_files']=not [p for p in out.rglob('*') if p.name.upper().startswith(('PCRX.','PCYM.'))]
 for name,data in [('serial.bin',peer.wire),('peer.bin',peer.sent)]:(out/name).write_bytes(data)
 (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n');(out/'frames.json').write_text(json.dumps(peer.frames,indent=2)+'\n');(out/'screen.txt').write_text('\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))+'\n')
 result=dict(passed=all(checks.values()),case=r['name'],direction=r['direction'],checks=checks,errors=peer.errors,binary_sha256=a.sha256,seconds=round(time.monotonic()-started,3),command=command,keys=' '.join(keys),headers=peer.headers,completed_sha256=peer.completed,scope='Actual DOS UI/BIOS/UART/files with independent Python YMODEM CRC/framing peer on isolated synthetic media. No product callbacks/terminal responses injected; no physical CTS/carrier timing claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(r['name'],'PASS' if result['passed'] else json.dumps(result),flush=True);return result

def self_check():
 assert crc16(b'123456789')==0x31c3
 for size in (128,1024):
  raw=payload(size);f=frame(raw,255);assert f[:3]==bytes([1 if size==128 else 2,255,0]) and int.from_bytes(f[-2:],'big')==crc16(raw)
 assert frame(payload(128),256)[1:3]==b'\x00\xff'
 assert header(b'X',0).startswith(b'X\0' + b'0\0') and header(b'X').startswith(b'X\0\0') and header()==bytes(128)
 assert b''.join(blocks(file('X',b'\x00\x1a\xff')))==b'\x00\x1a\xff'+b'\x1a'*125
 print('Independent CRC/header/block fixture self-check passed; no DOS runtime executed')
def main():
 if '--self-check' in __import__('sys').argv:self_check();return 0
 p=argparse.ArgumentParser();p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);p.add_argument('--case',action='append',default=[]);p.add_argument('--com',type=int,choices=range(1,5),default=1);p.add_argument('--baud',type=int,default=38400);p.add_argument('--flow',choices=['HARD','NONE'],default='HARD');p.add_argument('--after-ms',type=int,default=15000);p.add_argument('--timeout',type=int,default=100);p.add_argument('--jobs',type=int,choices=range(1,5),default=1);a=p.parse_args()
 assert a.label.replace('-','').replace('_','').isalnum();assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256,'Explicit frozen binary required'
 selected=[r for r in recipes() if not a.case or r['name'] in a.case];assert selected;OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with ThreadPoolExecutor(max_workers=a.jobs) as pool:rows=list(pool.map(lambda r:run_case(r,a),selected))
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,jobs=a.jobs,cases=rows);(OUT/a.label/'checks.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
