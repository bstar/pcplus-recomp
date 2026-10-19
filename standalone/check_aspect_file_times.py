#!/usr/bin/env python3
"""Native timestamp core with real decimal CRT and explicit stdio/kernel inputs."""
import argparse,hashlib,json,re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from check_aspect_enumeration import Machine as Base,DATA
from build_aspect_file_times import ROOT,OUT,sha

def number(raw):
 m=re.match(rb'[ \t]*([+-]?)([0-9]+)',raw)
 return (int(m[2])*(-1 if m[1]==b'-' else 1))&65535 if m else 0
def date_word(raw):
 b=bytearray(raw.ljust(81,b'\0'));b[2]=b[5]=0
 year=number(bytes(b[6:]).split(b'\0')[0]);year=year+20 if year<80 else year-80
 return ((year<<9)|(number(bytes(b).split(b'\0')[0])<<5)|number(bytes(b[3:]).split(b'\0')[0]))&65535
def time_word(raw):
 b=bytearray(raw.ljust(81,b'\0'));b[2]=0
 return ((number(bytes(b).split(b'\0')[0])<<11)|(number(bytes(b[3:]).split(b'\0')[0])<<5))&65535
class Machine(Base):
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.units=json.loads((OUT/'manifest.json').read_text())['units']
  for unit in self.units:
   code=original[unit['file_start']:unit['file_start']+unit['bytes']] if original else (ROOT/unit['output']).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def hook(self,u,at,size,data):
  self.seen.add(at);sp=u.reg_read(UC_X86_REG_SP);arg=lambda n:self.word(sp+2*n)
  if at==0x1f800:self.returned=True;u.emu_stop();return
  if any(0x10000+x['start']<=at<0x10000+x['end'] for x in self.units):return
  fn=at-0x10000
  if fn==0xdf04:self.ret(self.operands.pop(0))
  elif fn==0x841a:
   assert (arg(1),arg(2))==(0x5200,0x77a1);self.events.append('open');self.ret(0x5000 if self.opened else 0)
  elif fn==0x8318:
   assert arg(1)==0x5000;self.events.append('close');self.ret(self.close_result)
  elif fn==0x82b6:
   assert arg(1)==0x5300
   if arg(2)==0x77a4:text=f'{arg(3):2d}-{arg(4):02d}-{arg(5):02d}'
   else:assert arg(2)==0x77b2;text=f'{arg(3):02d}:{arg(4):02d}'
   u.mem_write(DATA+arg(1),text.encode()+b'\0');self.events.append('format');self.ret(len(text))
  else:raise AssertionError(('Unexpected boundary',hex(at)))
 def kernel(self,u,n,data):
  assert n==0x21 and u.reg_read(UC_X86_REG_BX)==9;fn=u.reg_read(UC_X86_REG_AX)
  if fn==0x5700:
   self.events.append('read');u.reg_write(UC_X86_REG_CX,self.clock);u.reg_write(UC_X86_REG_DX,self.date);error=self.read_error
  else:
   assert fn==0x5701;self.events.append('write');self.writes.append((u.reg_read(UC_X86_REG_CX),u.reg_read(UC_X86_REG_DX)));error=self.write_error
  u.reg_write(UC_X86_REG_AX,error or 0x8888);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags&~1)|bool(error))
 def run(self,kind,payload=b'03-07-93',opened=True,date=0x1a67,clock=0x6dbd,read_error=0,write_error=0,close_result=0):
  self.clock,self.date,self.opened,self.read_error,self.write_error,self.close_result=clock,date,opened,read_error,write_error,close_result
  self.events=[];self.writes=[];self.operands=[0x5200,0x5300];self.seen=set();self.returned=False;u=self.u
  before=bytearray((i*37+11)&255 for i in range(65536));before[0x5000:0x5008]=b'\0'*7+b'\x09';before[0x5200:0x5206]=b'X.DAT\0';before[0x5300:0x5351]=payload.ljust(81,b'\0');before[0x77a1:0x77a4]=b'rb\0'
  u.mem_write(DATA,bytes(before));self.put(0xf000,0xf800)
  args=[0x5300] if kind in ('date','time') else [9] if kind=='read' else [9,clock,date] if kind=='write' else []
  for i,v in enumerate(args):self.put(0xf002+2*i,v)
  for reg,val in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)):
   u.reg_write(reg,val)
  start={'getdate':0xed85,'gettime':0xed8c,'setdate':0xed94,'settime':0xed9c,'date':0xef37,'time':0xef84,'read':0xf2eb,'write':0xf2fc}[kind]
  u.emu_start(0x10000+start,0,count=20000);assert self.returned
  if kind in ('date','time') or (opened and kind in ('setdate','settime')):
   before[0x5302]=0
   if kind in ('date','setdate'):before[0x5305]=0
  if kind in ('date','time'):assert u.reg_read(UC_X86_REG_AX)==(date_word(payload) if kind=='date' else time_word(payload))
  elif kind in ('getdate','gettime','setdate','settime'):
   before[0xd124:0xd126]=int(not opened).to_bytes(2,'little');assert not self.operands
   if not opened:assert self.events==['open']
   else:
    assert self.events==['open','read',('format' if kind.startswith('get') else 'write'),'close']
    if kind=='getdate':text=f'{(date>>5)&15:2d}-{date&31:02d}-{((date>>9)+80)%100:02d}'.encode()+b'\0';before[0x5300:0x5300+len(text)]=text
    elif kind=='gettime':text=f'{clock>>11:02d}:{(clock>>5)&63:02d}'.encode()+b'\0';before[0x5300:0x5300+len(text)]=text
    elif kind=='setdate':assert self.writes==[(clock,date_word(payload))]
    else:assert self.writes==[(time_word(payload),date)]
  elif kind=='read':assert self.events==['read'] and u.reg_read(UC_X86_REG_AX)==clock and u.reg_read(UC_X86_REG_DX)==date
  else:assert self.events==['write'] and self.writes==[(clock,date)]
  after=bytes(u.mem_read(DATA,65536));assert after[:0xef00]==before[:0xef00] and after[0xf00a:]==before[0xf00a:],kind
  assert u.reg_read(UC_X86_REG_SP)==0xf002
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000 and not u.reg_read(UC_X86_REG_EFLAGS)&0x400
  return after[:0xef00],self.events,self.writes

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();raw=a.original.read_bytes() if a.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()==json.loads((ROOT/'standalone/fixtures/aspect_file_time_native_units.json').read_text())['original_sha256']
 models=[Machine()]+([Machine(raw)] if raw else []);count=0;seen=set()
 def case(kind,**kwargs):
  nonlocal count
  values=[m.run(kind,**kwargs) for m in models];assert all(v==values[0] for v in values);count+=1;seen.update(models[0].seen)
 for year in range(100):
  for month in (1,3,12):case('date',payload=f'{month:02d}-07-{year:02d}'.encode())
 for hour in range(24):
  for minute in (0,1,29,30,59):case('time',payload=f'{hour:02d}:{minute:02d}'.encode())
 for value in (b'',b'R',b'99-99-99',b'-1-07-93',b'00/00/00',b'12x31x79',b' 3-07-93',b'01-01-65535',b'12-31--1',b'R'*80):
  case('date',payload=value);case('time',payload=value)
 for date in (0,1,0x1a67,0x289f,0xff9f,0xffff):case('getdate',date=date)
 for clock in (0,1,29,0x6dbd,0xffff):case('gettime',clock=clock)
 for kind in ('getdate','gettime','setdate','settime'):
  for opened in (False,True):
   for error in (0,6,0xffff):
    for close in (0,0xffff):case(kind,opened=opened,read_error=error,write_error=error,close_result=close,payload=b'21:06' if kind=='settime' else b'03-07-93')
 for error in (0,1,6,0xffff):case('read',read_error=error);case('write',write_error=error)
 for unit in models[0].units:assert 0x10000+unit['start'] in seen
 report=dict(passed=True,cases=count,original_comparisons=count if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),reused_checker_sha256=sha(ROOT/'standalone/check_aspect_enumeration.py'),scope='Actual390 native timestamp and87 reused decimal CRT bytes. Explicit stdio/string operands/formatting/kernel boundary values,all00..99 year pivots,valid hours/minutes,malformed/short/80-byte parsing,destructive input offsets,open-failure consumption and ignored DOS/close error policy. Complete nonstack data/stack/register/DS=SS/DF and optional actual-original replay. Not actual DOS files,global writeback or source-preserving runtime adaptation.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Native file times:',count,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
