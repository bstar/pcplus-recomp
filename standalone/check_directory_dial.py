#!/usr/bin/env python3
"""Actual DOS code tests, synthetic strings/codes/record data only."""
import hashlib,json,random,struct
from pathlib import Path
from dos_image import DosImage
from unicorn.x86_const import UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BX
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/directory-dial/DIRDIAL.EXE'
def upper(s):return bytes(x-32 if 97<=x<=122 else x for x in s)
def legacy(number,codes):return b''.join(codes[x-65] if 65<=x<=74 else bytes([x]) for x in upper(number))
class Dial(DosImage):
 def __init__(self,number=b'',codes=None):
  super().__init__(BINARY,BINARY.parent/'directory_dial.map');self.codes=codes or [b'']*10
  self.uc.mem_write(self.symbols['directory_dial_codes'],b''.join(x+b'\0'*(25-len(x)) for x in self.codes));self.uc.mem_write(self.symbols['directory_dial_input'],number+b'\0')
 def expand(self,mode):
  return self.call('_directory_number_expand',[self.offset('directory_dial_input'),self.offset('directory_dial_codes'),self.offset('directory_dial_output'),mode])
 def output(self):return bytes(self.uc.mem_read(self.symbols['directory_dial_output'],64))

def main():
 cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n)
 def random():
  rng=__import__('random').Random(201);count=0
  for _ in range(256):
   number=bytes(rng.randrange(1,256) for _ in range(rng.randrange(21)));codes=[bytes(rng.randrange(1,256) for _ in range(rng.randrange(25))) for _ in range(10)]
   for mode in (0,1):
    d=Dial(number,codes);old=d.output();want=number if mode==0 else legacy(number,codes);status=d.expand(mode)
    assert status==(0 if len(want)<=60 else 4)
    assert d.output()==(want+b'\0'+old[len(want)+1:] if status==0 else old)
    for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert d.uc.reg_read(reg)==value
    assert bytes(d.uc.mem_read(d.symbols['directory_dial_output']-2,2))==b'\x5a\xa5' and bytes(d.uc.mem_read(d.symbols['directory_dial_output']+64,2))==b'\xa5\x5a';count+=1
  return count
 check('cdecl-literal-and-legacy-random-atomic-expansion',random)
 def semantics():
  for number,codes,want in [(b'lab.local:23232',[b'']*10,b'L.LOL:23232'),(b'Aj',[b'abc']+[b'']*8+[b'xyz'],b'abcxyz'),(b'AA',[b'J']+[b'']*9,b'JJ')]:
   d=Dial(number,codes);assert d.expand(1)==0 and d.output().split(b'\0')[0]==want,(number,d.output(),want)
  d=Dial(b'A'*20,[b'123']+[b'']*9);assert d.expand(1)==0 and d.output()[:61]==b'123'*20+b'\0'
  return 4
 check('uppercase-code-range-nonrecursive-content-and-sixty-byte-boundary',semantics)
 def errors():
  for mode,source,malformed,want in [(1,b'X'*21,False,2),(1,b'K',True,3),(1,b'A'*20,False,4),(2,b'X',False,5)]:
   d=Dial(source,[b'X'*24]+[b'']*9)
   if malformed:d.uc.mem_write(d.symbols['directory_dial_codes']+225,b'X'*25)
   old=d.output();assert d.expand(mode)==want and d.output()==old
  d=Dial(b'Case.Host');d.uc.mem_write(d.symbols['directory_dial_codes']+225,b'X'*25);assert d.expand(0)==0 and d.output().startswith(b'Case.Host\0')
  for args in [(65535,0,128,0),(0,65535,128,1),(0,0,65535,0)]:
   d=Dial();old=d.output();assert d.call('_directory_number_expand',args)==1 and d.output()==old
  return 8
 check('malformed-mode-overflow-pointer-errors-and-literal-unused-header',errors)
 def original():
  d=Dial();d.uc.mem_write(d.symbols['directory_dial_codes'],b'9,\0');d.uc.mem_write(d.symbols['directory_dial_codes']+25,b',0\0');d.uc.mem_write(d.symbols['directory_dial_records']+25,b'55b\0');d.uc.mem_write(d.symbols['directory_dial_tokens'],b'a1b\0')
  result=d.call('directory_dial_expand_original',[0,d.offset('directory_dial_output')]);assert result==1 and d.output().startswith(b'9,55,0,0\0')
  assert bytes(d.uc.mem_read(d.symbols['directory_dial_tokens'],4))==b'A1B\0';assert bytes(d.uc.mem_read(d.symbols['directory_dial_record']+25,4))==b'55B\0'
  return 1
 check('actual-original-quickdial-prefix-record-number-suffix-and-inplace-uppercase',original)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked original quickdial plus bounded maintained C ABI number helper; synthetic in-memory records, no directory/PRM/UART.'};(BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
