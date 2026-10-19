#!/usr/bin/env python3
"""Native enumeration instructions with explicit DOS/string/format boundaries."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_enumeration import ROOT,OUT,sha
DATA=0x30000
class Machine:
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.units=json.loads((OUT/'manifest.json').read_text())['units']
  for unit in self.units:
   code=original[unit['file_start']:unit['file_start']+unit['bytes']] if original else (ROOT/unit['output']).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def word(self,at):return int.from_bytes(self.u.mem_read(DATA+at,2),'little')
 def put(self,at,value):self.u.mem_write(DATA+at,(value&65535).to_bytes(2,'little'))
 def string(self,at):return bytes(self.u.mem_read(DATA+at,128)).split(b'\0')[0]
 def ret(self,value=0,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);ip=self.word(sp);self.u.reg_write(UC_X86_REG_AX,value&65535);self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup);self.u.reg_write(UC_X86_REG_IP,ip)
 def hook(self,u,at,size,data):
  self.seen.add(at);sp=u.reg_read(UC_X86_REG_SP);arg=lambda n:self.word(sp+2*n)
  if at==0x1f800:self.returned=True;u.emu_stop();return
  if any(0x10000+x['start']<=at<0x10000+x['end'] for x in self.units):return
  fn=at-0x10000
  if fn==0xdf04:self.ret(self.operands.pop(0))
  elif fn==0xe0e4:self.ret(self.option)
  elif fn==0x4efb:self.warnings.append(arg(1));self.ret(cleanup=2)
  elif fn==0x8268:
   self.u.mem_write(DATA+arg(1),self.string(arg(2))+b'\0');self.ret(arg(1))
  elif fn==0x8c2a:
   pos=self.string(arg(1)).find(bytes([arg(2)&255]));self.ret(arg(1)+pos if pos>=0 else 0)
  elif fn==0x85b4:
   self.u.mem_write(DATA+arg(1),bytes(self.u.mem_read(DATA+arg(2),arg(3))));self.ret(arg(1))
  elif fn==0x9476:
   a,b=self.string(arg(1)),self.string(arg(2));self.ret((a>b)-(a<b))
  elif fn==0x82b6:
   assert arg(1)==0xce3e and arg(3)==0xced2
   name=self.string(arg(3)).decode('ascii')
   if arg(2)==0x5d87:
    month,day,year,hour,minute=[arg(i) for i in range(4,9)]
    text=f'{name:<12s}   <DIR>  {month:2d}-{day:02d}-{year:02d}  {hour:02d}:{minute:02d}'
   else:
    assert arg(2)==0x5daf
    size=arg(4)+(arg(5)<<16);month,day,year,hour,minute=[arg(i) for i in range(6,11)]
    text=f'{name:<12s}  {size:6d}  {month:2d}-{day:02d}-{year:02d}  {hour:02d}:{minute:02d}'
   u.mem_write(DATA+arg(1),text.encode()+b'\0');self.ret(len(text))
  else:raise AssertionError(('Unexpected boundary',hex(at)))
 def kernel(self,u,n,data):
  assert n==0x21;ah=u.reg_read(UC_X86_REG_AX)>>8;self.kernel_calls.append(ah)
  if ah==0x1a:self.dta=u.reg_read(UC_X86_REG_DX);return
  assert ah in (0x4e,0x4f) and self.dta==0xceb4
  if ah==0x4e:
   assert u.reg_read(UC_X86_REG_CX)==self.mask
   assert self.string(u.reg_read(UC_X86_REG_DX))==b'*.ZIP'
  if self.found:
   record=bytearray(43);record[21]=self.attribute;struct.pack_into('<HHI',record,22,self.time,self.date,self.size);record[30:30+len(self.name)+1]=self.name+b'\0';u.mem_write(DATA+self.dta,bytes(record))
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags&~1)|(not self.found));u.reg_write(UC_X86_REG_AX,0 if self.found else 18)
 def run(self,kind,*,attrs=b'',mode=1,attribute=0x20,name=b'ONE.ZIP',found=True,size=1234,date=(13<<9)|(10<<5)|7,time=(13<<11)|(45<<5),option=0):
  self.option=option;self.attribute=attribute;self.name=name;self.found=found;self.size=size;self.date=date;self.time=time
  self.mask=1 if not option else sum(bit for letter,bit in ((b'R',1),(b'H',2),(b'S',4),(b'A',32),(b'D',16),(b'V',8)) if letter in attrs.upper())
  self.seen=set();self.warnings=[];self.kernel_calls=[];self.operands=[0x6000]+([0x6100] if option else []);self.returned=False;self.dta=0xceb4
  u=self.u;before=bytearray((i*37+11)&255 for i in range(65536))
  before[0x6000:0x6006]=b'*.ZIP\0';before[0x6100:0x6100+len(attrs)+1]=attrs+b'\0'
  before[0x4942]=0;before[0x77bc:0x77c1]=b'.\0..\0'
  before[0x7caf:0x7daf]=bytes(2 if 97<=i<=122 else 0 for i in range(256))
  # Controlled stale fields establish that unsuccessful searches preserve them.
  before[0xce3e:0xce6a]=b'OLD\0'+b' '*40;before[0xe132:0xe139]=b'OLD\0\0\0\0'
  before[0xe130:0xe132]=(0x4942).to_bytes(2,'little')
  before[0xe39c:0xe39e]=(0x4567).to_bytes(2,'little')
  args=[]
  start={'first':0xefb0,'next':0xefe8,'parse':0xeda4,'attributes':0xee23,'size':0xda6a,'getattr':0xdac5,'getdate':0xdac9,'getext':0xdadb,'getname':0xdadf,'getbase':0xdae3,'gettime':0xdae7}[kind]
  if kind=='parse':args=[mode,0x6100]
  if kind=='attributes':args=[0xe132,attribute]
  u.mem_write(DATA,bytes(before));self.put(0xf000,0xf800)
  for i,v in enumerate(args):self.put(0xf002+i*2,v)
  for reg,val in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)):
   u.reg_write(reg,val)
  u.emu_start(0x10000+start,0,count=10000);assert self.returned
  after=bytes(u.mem_read(DATA,65536));allowed=[(0xef00,0xf006)]
  if kind in ('first','next'):
   assert self.word(0xe39c)==int(found)
   if kind=='first':assert self.string(0xce6a)==b'*.ZIP'
   assert self.kernel_calls==([0x1a,0x4e] if kind=='first' else [0x4f])
   if found:
    assert self.string(0xe132)==b''.join(c for c,bit in ((b'R',1),(b'H',2),(b'S',4),(b'A',32),(b'D',16),(b'V',8)) if attribute&bit)
    if not attribute&8:
     assert self.string(0xced2)==name
     expected=name if name in (b'.',b'..') and attribute&16 else name.split(b'.',1)[0]
     assert self.string(0xce3e)==expected,(kind,attribute,name,self.string(0xce3e),expected)
     assert self.string(self.word(0xe130))==(name.split(b'.',1)[1] if b'.' in name and expected!=name else b'')
    else:
     assert self.string(0xced2)==name.replace(b'.',b'')
     if b'.' not in name:
      assert after[:12]==before[1:13]
      allowed += [(0,12)]
    assert int.from_bytes(after[0xcece:0xced2],'little')==size
   else:assert self.string(0xce3e)==b'OLD' and self.string(0xe132)==b'OLD'
   allowed += [(0xce3e,0xce6a),(0xce6a,0xce6a+81),(0xceb4,0xcedf),(0xe130,0xe139),(0xe39c,0xe39e),(0x5d86,0x5d87)]
  elif kind=='parse':
   mask=0;warnings=[]
   for c in attrs.upper():
    bit={82:1,72:2,83:4,65:32,68:16,86:8}.get(c)
    if bit is None or (c in (68,86) and not mode):warnings.append(0)
    else:mask|=bit
   assert u.reg_read(UC_X86_REG_AX)==mask and self.warnings==warnings,(attrs,mode)
  elif kind=='attributes':
   assert self.string(0xe132)==b''.join(c for c,bit in ((b'R',1),(b'H',2),(b'S',4),(b'A',32),(b'D',16),(b'V',8)) if attribute&bit)
   allowed += [(0xe132,0xe139)]
  else:
   expected={'getattr':0xe132,'getdate':0xce54+1,'getext':0x4942,'getname':0xced2,'getbase':0xce3e,'gettime':0xce5e}
   if kind in expected:assert u.reg_read(UC_X86_REG_AX)==expected[kind]
   else:assert u.reg_read(UC_X86_REG_AX)==self.word(0xcece) and u.reg_read(UC_X86_REG_DX)==self.word(0xced0)
  for i,(a,b) in enumerate(zip(before,after)):
   if a!=b:assert any(lo<=i<hi for lo,hi in allowed),(kind,hex(i))
  assert u.reg_read(UC_X86_REG_SP)==0xf002+(len(args)*2)
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000 and not u.reg_read(UC_X86_REG_EFLAGS)&0x400
  return after[:0xef00],self.warnings,self.kernel_calls

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);args=p.parse_args();raw=args.original.read_bytes() if args.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()==json.loads((ROOT/'standalone/fixtures/aspect_enumeration_native_units.json').read_text())['original_sha256']
 models=[Machine()]+([Machine(raw)] if raw else []);cases=0;seen=set()
 def case(kind,**kwargs):
  nonlocal cases
  outputs=[m.run(kind,**kwargs) for m in models];assert all(o==outputs[0] for o in outputs);cases+=1;seen.update(models[0].seen)
 for c in range(1,256):
  for mode in (0,1):case('parse',attrs=bytes([c]),mode=mode)
 for attrs in (b'',b'RHSA',b'rhsadv',b'RrR?dV',b'R'*80):
  for mode in (0,1):case('parse',attrs=attrs,mode=mode)
 for attr in range(256):case('attributes',attribute=attr)
 for kind in ('first','next'):
  for found in (False,True):
   for attribute,name in ((0,b'ONE.ZIP'),(1,b'ONE'),(0x20,b'LONGNAME.ZIP'),(0x10,b'.'),(0x10,b'..'),(0x10,b'DIR.ZIP'),(0x11,b'DIR.ZIP'),(8,b'VOLUME.LBL')):
    for option,attrs in ((0,b''),(1,b''),(1,b'rhsadv')):case(kind,found=found,attribute=attribute,name=name,option=option,attrs=attrs)
 for size in (0,999999,1000000,0x7fffffff,0xffffffff):case('first',size=size)
 case('first',attribute=8,name=b'VOLUME')
 for kind in ('size','getattr','getdate','getext','getname','getbase','gettime'):case(kind)
 for unit in models[0].units:assert 0x10000+unit['start'] in seen
 report=dict(passed=True,cases=cases,original_comparisons=cases if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),scope='Actual675 native instruction bytes, explicit DOS21 DTA/results and CRT/operand boundaries. All attribute input bytes,format masks,missing search/next,default/explicit flags,files/directories/dot entries/volume formatting,large sizes,getter pointers and original no-dot volume null write. Complete nonstack DS write admission,stack/register/DS=SS/DF and optional byte-identical original replay. Not actual DOS kernel,DTA restoration or application integration.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Native enumeration:',cases,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
