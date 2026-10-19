#!/usr/bin/env python3
"""Execute recovered file handlers with explicit operand/CRT boundary models."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-script-files';DATA=0x30000

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Machine:
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.units=json.loads((OUT/'manifest.json').read_text())['units']
  for unit in self.units:
   code=original[unit['file_start']:unit['file_start']+unit['bytes']] if original else (OUT/(unit['name']+'.bin')).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def word(self,offset):return int.from_bytes(self.u.mem_read(DATA+offset,2),'little')
 def put(self,offset,value):self.u.mem_write(DATA+offset,(value&65535).to_bytes(2,'little'))
 def string(self,offset):return bytes(self.u.mem_read(DATA+offset,81)).split(b'\0')[0]
 def ret(self,value=0,cleanup=0,high=None):
  u=self.u;sp=u.reg_read(UC_X86_REG_SP);ip=self.word(sp);u.reg_write(UC_X86_REG_AX,value&65535)
  if high is not None:u.reg_write(UC_X86_REG_DX,high&65535)
  u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ip)
 def hook(self,u,at,size,data):
  self.visited.add(at)
  if at==0x1f800:self.returned=True;u.emu_stop();return
  sp=u.reg_read(UC_X86_REG_SP)
  arg=lambda n:self.word(sp+2*n)
  fn=at-0x10000
  if fn==0xdd68:
   bounds=(arg(1),arg(2));assert bounds in ((5,0),(2,0)),bounds
   value=self.slot if bounds==(5,0) else self.origin;self.events.append(('range',*bounds,value));self.ret(value,4)
  elif fn==0x4efb:
   assert arg(1)==4;self.events.append(('warning',4));self.ret(0,2)
  elif fn==0xdf04:
   pointer=self.strings.pop(0);self.events.append(('string',pointer));self.ret(pointer)
  elif fn==0xdf0b:self.events.append(('destination',));self.ret(0x5600)
  elif fn==0xe0a4:self.events.append(('flush-destination',));self.ret()
  elif fn in (0xdde3,0xde11):self.events.append(('word' if fn==0xdde3 else 'count',));self.ret(self.number if fn==0xdde3 else self.count)
  elif fn==0xde3a:self.put(0x5700,arg(1));self.events.append(('write-integer',arg(1)));self.ret(0,2)
  elif fn==0xdcc1:self.events.append(('long',));self.ret(self.position,high=self.position>>16)
  elif fn==0xde92:self.events.append(('long-destination',));self.ret(0x5800)
  elif fn==0x8268:
   assert (arg(1),arg(2))==(0x5500,0x5400);self.u.mem_write(DATA+arg(1),self.string(arg(2))+b'\0');self.events.append(('strcpy',));self.ret(arg(1))
  elif fn==0x9be8:
   assert arg(1)==0x5500;self.u.mem_write(DATA+arg(1),self.string(arg(1)).lower()+b'\0');self.events.append(('strlwr',));self.ret(arg(1))
  elif fn==0x8d18:self.events.append(('strlen',));self.ret(len(self.string(arg(1))))
  elif fn in (0x8318,0x8c54,0x998a,0x8ed8):
   assert arg(1)==0x5000;name={0x8318:'close',0x8c54:'flush',0x998a:'getc',0x8ed8:'tell'}[fn]
   self.events.append((name,));self.ret(self.result,high=self.result>>16 if fn==0x8ed8 else None)
  elif fn==0x841a:
   assert (arg(1),arg(2))==(0x5300,0x5500);assert self.string(arg(1))==b'OWNED.DAT' and self.string(arg(2))==b'rb'
   self.events.append(('open',));self.ret(self.result)
  elif fn in (0x8436,0x8e88):
   assert arg(2)==0x5000
   assert arg(1)==(self.number&65535) if fn==0x8436 else arg(1)==0x5600
   self.events.append(('putc' if fn==0x8436 else 'puts',arg(1)));self.ret(self.result)
  elif fn==0x99a8:
   assert (arg(1),arg(2),arg(3))==(0x5600,81,0x5000)
   self.u.mem_write(DATA+0x5600,self.payload+b'\0');self.events.append(('gets',));self.ret(0x5600 if self.result else 0)
  elif fn in (0x845a,0x86ac):
   assert (arg(1),arg(2),arg(3),arg(4))==(0x5600,1,self.count,0x5000)
   if fn==0x845a:self.u.mem_write(DATA+0x5600,self.payload[:self.count]);value=min(len(self.payload),self.count)
   else:value=self.result
   self.events.append(('read' if fn==0x845a else 'write',));self.ret(value)
  elif fn==0x853a:
   assert (arg(1),arg(2),arg(3),arg(4))==(0x5000,self.position&65535,(self.position>>16)&65535,self.origin)
   self.events.append(('seek',));self.ret(self.result)
 def run(self,name,slot=0,flags=0,result=0,keep=0,text=0,payload=b'ABC\r\n',count=3,opened=True,check=1,position=0x12345678,origin=0):
  u=self.u;u.mem_write(DATA,b'\xa5'*65536);self.slot=slot;self.result=result;self.number=65;self.count=count;self.position=position;self.origin=origin;self.payload=payload
  self.events=[];self.visited=set();self.returned=False;self.strings=[0x5300,0x5400] if name=='open' else [0x5600]
  self.put(0xe39e+slot*2,0x5000 if opened else 0);self.put(0xe3aa,0xa55a);self.put(0xe37c,check);self.put(0xe388,keep);self.put(0xd124,0x9abc);self.put(0x4b06,0x5500)
  u.mem_write(DATA+0x5000,b'\0'*8);u.mem_write(DATA+0x5006,bytes([flags,7]));u.mem_write(DATA+0x7b2b+7,bytes([text]))
  for offset,value in [(0x5300,b'OWNED.DAT\0'),(0x5400,b'RB\0'),(0x5500,b'untouched\0'),(0x5600,b'Z'*81)]:u.mem_write(DATA+offset,value)
  self.put(0x5700,0xa55a);self.put(0x5800,0xa55a);self.put(0x5802,0xa55a);self.put(0xf200,0xf800)
  direct=name in ('status','lookup','number')
  if name=='status':self.put(0xf202,0x5000)
  before=bytes(u.mem_read(DATA,65536))
  for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000),(UC_X86_REG_SP,0xf200),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,2)]:u.reg_write(reg,value)
  entry=next(x['start'] for x in self.units if x['name']==name)
  u.emu_start(0x10000+entry,0x20000,count=2000);assert self.returned,(name,self.events)
  assert u.reg_read(UC_X86_REG_SP)==0xf202+(2 if name=='status' else 0)
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS)]==[0xbabe,0x1234,0x5678,0x3000,0x3000]
  assert not u.reg_read(UC_X86_REG_EFLAGS)&0x400
  expected=bytearray(before);status=0x9abc
  if name not in ('status',):expected[0xe3aa:0xe3ac]=slot.to_bytes(2,'little')
  if name=='clear':expected[0x5006]=flags&0xcf
  elif name=='close':expected[0xe39e+2*slot:0xe3a0+2*slot]=b'\0\0';status=result&65535
  elif name=='open':
   expected[0xe39e+2*slot:0xe3a0+2*slot]=(result&65535).to_bytes(2,'little');expected[0x5500:0x5503]=b'rb\0';status=int(result==0)
   assert [e[0] for e in self.events].count('close')==int(opened)
   assert [e[0] for e in self.events].index('strlwr')<[e[0] for e in self.events].index('open')
  elif name=='seek':status=result&65535
  elif name in ('status','flush','getc','gets','putc','puts','read','write'):status=flags&32
  if name in ('getc','eof'):expected[0x5700:0x5702]=((flags&16) if name=='eof' else result&65535).to_bytes(2,'little')
  if name=='tell':expected[0x5800:0x5804]=(result&0xffffffff).to_bytes(4,'little')
  if name=='read':
   n=min(count,len(payload));expected[0x5600:0x5600+n]=payload[:n];expected[0x5600+n]=0;expected[0x5700:0x5702]=n.to_bytes(2,'little')
  if name=='gets':
   value=bytearray(payload+b'\0')
   if not result:value[0]=0
   elif not keep and payload:
    if payload.endswith(b'\n'):
     at=len(payload)-1
     if not text and len(payload)>=2 and payload[-2]==13:at-=1
     value[at]=0
    elif not text and payload.endswith(b'\x1a') and flags&16:value[-2]=0
   expected[0x5600:0x5600+len(value)]=value
  expected[0xd124:0xd126]=status.to_bytes(2,'little')
  after=bytes(u.mem_read(DATA,65536));assert after[:0xf000]==expected[:0xf000] and after[0xf206:]==expected[0xf206:],(name,flags,result,keep,text,payload)
  if name in ('gets','read'):assert [e[0] for e in self.events].count('flush-destination')==1
  if name=='lookup':
   assert u.reg_read(UC_X86_REG_AX)==(0x5000 if opened else 0x7b7a if check else 0)
   assert ('warning',4) in self.events if not opened and check else ('warning',4) not in self.events
  if name=='number':assert u.reg_read(UC_X86_REG_AX)==slot
  return after[:0xf000],tuple(self.events),u.reg_read(UC_X86_REG_SP)

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();raw=a.original.read_bytes() if a.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 machines=[Machine()]+([Machine(raw)] if raw else []);count=0;seen=set()
 def case(name,**kw):
  nonlocal count
  results=[m.run(name,**kw) for m in machines];assert all(r==results[0] for r in results);seen.update(machines[0].visited);count+=1
 for slot,flags in itertools.product(range(6),range(256)):
  for name in ('clear','status','eof'):case(name,slot=slot,flags=flags)
 for slot,flags,result in itertools.product(range(6),(0,16,32,48,255),(0,1,255,65535)):
  for name in ('close','flush','getc','putc','puts','write','tell'):case(name,slot=slot,flags=flags,result=result)
 for slot,opened,result in itertools.product(range(6),(False,True),(0,0x5000)):
  case('open',slot=slot,opened=opened,result=result)
 for slot,opened,check in itertools.product(range(6),(False,True),(0,1)):
  case('lookup',slot=slot,opened=opened,check=check);case('number',slot=slot)
 for flags,keep,text,payload,result in itertools.product((0,16,32,48),(0,1),(0,128),(b'',b'A',b'A\n',b'A\r\n',b'\n',b'\r\n',b'A\x1a',b'Z'*80),(0,1)):
  case('gets',flags=flags,keep=keep,text=text,payload=payload,result=result)
 for count_,payload in itertools.product((0,1,3,80),(b'',b'ABC',b'A\0B',b'Z'*80)):
  case('read',count=count_,payload=payload)
 for origin,position,result in itertools.product(range(3),(0,1,-1,0x7fffffff,-0x80000000),(0,-1)):
  case('seek',origin=origin,position=position,result=result)
 for result in (0x10000,0x12345678,0x1234ffff,0x7fffffff,-1,-0x80000000):
  case('tell',result=result)
 assert all(0x10000+unit['start'] in seen for unit in machines[0].units)
 report=dict(passed=True,cases=count,original_comparisons=count if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),scope='Actual recovered13 file handlers and3 helpers with explicit operand/CRT/string/error-return models. Native slot-table, comparison, EOF destination, CRLF/controlZ and byte/count/long destination effects; full nonstack DS, stack and BP/SI/DI/DS=SS/DF checks. Models do not prove real stdio, fatal unwind, filesystem, arbitrary bytecode or integrated application behavior.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Native ASPECT script files:',count,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
