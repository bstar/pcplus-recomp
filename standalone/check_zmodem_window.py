#!/usr/bin/env python3
"""Independent reactive peer checks for bounded maintained ZMODEM sending."""
import ctypes as C,hashlib,json,subprocess,sys
from pathlib import Path
from check_zmodem import Fixture,Session,h,meta,send_meta,ROOT
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import header,packet
OUT=ROOT/'build/zmodem-window'

class WindowPeer(Fixture):
 def __init__(self,lib,body,*,fmt=67,capacity=0,flags=3,policy='delayed',recover=None,at=1536,source_fault=None):
  self.source_fault=source_fault;self.body=body;self.fmt=fmt;self.capacity=capacity;self.flags=flags;self.policy=policy;self.recover=recover;self.recovery_at=at
  self.buffer=bytearray();self.mode=None;self.cursor=0;self.segment=0;self.file=bytearray();self.recovered=0
  self.packets=[];self.headers=[];self.reads=[];self.snapshots=[];self.eofs=0;self.partial=False;self.must_sync=False;self.open_frame=False
  self.max_outstanding=0;self.max_segment=0;self.saw_cancel=False
  super().__init__(lib,h(1,((32 if fmt==67 else 0)|flags)<<24|capacity),[('TEST.BIN',body)])
  if source_fault=='close':self.fault='close'
 def seek(self,ctx,offset):
  if self.source_fault=='seek' and len(self.packets)>=3:return 1
  return super().seek(ctx,offset)
 def file_read(self,ctx,data,n,got):
  if self.source_fault=='read' and len(self.packets)>=3:return 1
  return super().file_read(ctx,data,n,got)
 def reply(self,raw,split=False):
  if split:
   for v in raw:self.rx.extend((v,65535))
  else:self.rx.extend(raw)
 def read(self,ctx,seconds):
  self.reads.append(seconds)
  # WAIT in a fragmented response means unavailable at this zero-wait poll;
  # a blocking read may wait for the next fragment, not time out immediately.
  while seconds and self.rx and self.rx[0]==65535:self.rx.pop(0)
  return super().read(ctx,seconds)
 def write(self,ctx,data,n):
  value=C.string_at(data,n);self.tx.extend(value)
  if value==bytes([24])*8+bytes([8])*10:self.saw_cancel=True;return 0
  if value==b'OO':assert self.headers[-1]['type']==8;return 0
  self.buffer.extend(value)
  while self.buffer:
   raw=bytes(self.buffer)
   if self.mode is None:
    item=header(raw,0);self.headers.append(item);del self.buffer[:item['end']]
    t=item['type']
    if t==0:pass
    elif t==4:self.mode='metadata'
    elif t==10:
     assert not self.open_frame;self.cursor=item['position'];assert self.cursor<=len(self.file)
     self.open_frame=True;self.mode='data'
    elif t==11:
     self.eofs+=1;assert item['position']==len(self.body) and bytes(self.file)==self.body
     if self.recover=='EOF' and not self.recovered:
      self.recovered+=1;self.reply(h(9,self.recovery_at));self.must_sync=True;self.segment=0
     else:self.reply(h(1,((32 if self.fmt==67 else 0)|self.flags)<<24|self.capacity))
    elif t==8:self.reply(h(8))
    elif t==3:pass
    else:raise AssertionError(('Unexpected sender header',t))
   else:
    item=packet(raw,0,self.fmt);del self.buffer[:item['end']]
    data=item['payload'];ending=item['ending']
    if self.mode=='metadata':
     assert data==send_meta('TEST.BIN',len(self.body)).ljust(128,b'\0') and ending==107
     self.reply(h(9));self.mode=None;self.must_sync=True
    else:
     if not data:
      assert ending==104;self.mode=None;self.open_frame=False;continue
     assert data==self.body[self.cursor:self.cursor+len(data)]
     self.snapshots.append(dict(sent=self.cursor+len(data),confirmed=self.session.position,ending=ending))
     outstanding=self.cursor+len(data)-self.session.position
     assert outstanding<=self.session.window
     self.max_outstanding=max(self.max_outstanding,outstanding)
     self.file[self.cursor:self.cursor+len(data)]=data;self.cursor+=len(data);self.segment+=len(data)
     self.max_segment=max(self.max_segment,self.segment)
     if self.capacity:assert self.segment<=self.capacity,'ACK released disk buffer capacity'
     if self.must_sync:assert ending==107;self.must_sync=False
     self.packets.append(dict(length=len(data),ending=ending,position=self.cursor))
     if ending in (104,107):self.mode=None;self.open_frame=False
     inject=self.recover and self.recover!='EOF' and (not self.recovered or self.recover=='repeat') and len(self.packets)>=3
     if inject:
      self.recovered+=1
      if self.recover=='cancel':self.reply(bytes([24])*5)
      elif self.recover=='future-ACK':self.reply(h(3,self.cursor+1))
      elif self.recover=='beyond-EOF':self.reply(h(9,len(self.body)+1))
      else:
       self.reply(h(9,self.recovery_at));self.must_sync=True
       if self.recovery_at>len(self.file):self.file[:self.recovery_at]=self.body[:self.recovery_at]
      self.segment=0
     elif ending==107:
      if self.policy=='stall' or self.policy=='lost-first-ACK' and len(self.packets)==1:
       self.segment=0;continue
      if self.policy=='duplicate-flood':self.reply(h(3,0)*20);self.segment=0;continue
      if self.policy=='wire-noise':self.reply(b'x'*32768);self.segment=0;continue
      if self.policy=='stale':self.reply(h(3,max(0,self.cursor-1)))
      self.reply(h(3,self.cursor));self.segment=0
     elif ending==106 and self.policy!='delayed':
      if self.policy=='stale':self.reply(h(3,max(0,self.session.position)))
      self.reply(h(3,self.cursor),self.policy=='fragmented')
     if self.policy=='early-init' and len(self.packets)==2:self.reply(h(1,0x23000000))
  return 0

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 files=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem.h','zmodem_wire.c','zmodem_wire.h','zmodem_name.c','zmodem_name.h','batch_header.c','batch_header.h')]
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in files if p.suffix=='.c'],'-o',str(OUT/'session.so')],check=True)
 lib=C.CDLL(str(OUT/'session.so'));lib.zm_run.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
 return lib,files

def main():
 lib,files=build();cases=[]
 def run(label,n=18001,expected=0,**options):
  body=(bytes(range(256))*((n+255)//256))[:n];f=WindowPeer(lib,body,**options);result=f.run(True)
  assert result==expected,(label,result,f.errors,f.events[-10:])
  assert sum(e[0]=='close' for e in f.events)==1
  if options.get('source_fault')=='close':assert f.session.owned==2 and f.session.cleanup_status
  else:assert f.source is None
  if not result:
   assert f.session.files==1 and f.session.bytes==n and f.session.position==n and bytes(f.file)==body and not f.buffer and not f.rx
  else:assert f.saw_cancel and f.session.files==0
  row=dict(case=label,passed=True,status=result,packets=len(f.packets),max_outstanding=f.max_outstanding,max_segment=f.max_segment,terminators=sorted({p['ending'] for p in f.packets}),polls=f.reads.count(0),recoveries=f.recovered,EOFs=f.eofs)
  cases.append(row);return f
 for fmt in (65,67):
  for n in (0,1,1023,1024,1025,8191,8192,8193,9216,9217,16384,16385,65797):run(f'delayed-{fmt}-{n}',n,fmt=fmt)
 for capacity in (1,127,1023,1024,1025,2049,4096,65535):
  for policy in ('delayed','immediate','fragmented'):
   run(f'capacity-{capacity}-{policy}',n=70001 if capacity==65535 else 18001,capacity=capacity,policy=policy)
 for flags in (0,1,2,3):
  f=run('capabilities-'+str(flags),flags=flags)
  assert (f.max_outstanding>1024)==(flags==3)
 for policy in ('immediate','fragmented','stale','early-init'):run('control-'+policy,policy=policy)
 for at in (0,1536,3072,18001):run('open-recovery-'+str(at),recover='open',at=at)
 for at in (0,1536,18001):run('EOF-recovery-'+str(at),recover='EOF',at=at)
 run('repeated-position-bounded',recover='repeat',at=0,expected=4)
 run('future-ACK-rejected',recover='future-ACK',expected=6)
 run('beyond-EOF-rejected',recover='beyond-EOF',expected=6)
 run('raw-CAN-cancels-open-frame',recover='cancel',expected=5)
 run('lost-first-boundary-ACK-replayed',policy='lost-first-ACK')
 for policy in ('stall','duplicate-flood','wire-noise'):run('bounded-'+policy,policy=policy,expected=4)
 for fault in ('seek','read','close'):run('window-source-fault-'+fault,source_fault=fault,expected=7)
 run('long-synchronous-prefix-replay',n=32769,flags=2,policy='immediate',recover='EOF',at=0)
 run('long-verified-prefix-replay',n=131073,capacity=4096,policy='immediate',recover='EOF',at=0)
 f=run('confirmed-progress-not-wire-cursor');assert any(p['sent']-p['confirmed']>=8192 for p in f.snapshots)
 files += [Path(__file__).resolve(),ROOT/'standalone/check_zmodem.py',ROOT/'lab/bbs/audit_zmodem.py']
 result=dict(passed=True,cases=cases,inputs=len(cases),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Independent reactive Python CRC/header/data peer; host C callbacks, full duplex/overlap and finite-capacity policy, delayed/fragmented/stale ACK, window and buffer invariants, midstream/EOF recovery, future ACK, raw CAN and confirmed-progress separation. No actual DOS/UART/BBS or physical timing claim.')
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'windowed sender cases')
if __name__=='__main__':main()
