#!/usr/bin/env python3
"""Native ASPECT comparison/assignment CPU diagnostics with explicit dependencies.

Maintained predicates and overlap-safe copy execute native instructions. Operand
and application services are controlled fixture callbacks, not a new evaluator.
Float callbacks either stop as unavailable or return opaque sentinel bytes only
for branch/copy observation; they do not implement floating-point arithmetic.
Optional --original compares the exact retained original code range separately.
"""
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
import random
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,
 UC_X86_REG_IP,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,
 UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_EFLAGS)
from build_aspect_operations import ROOT,OUT,START,END,SHA,FILE_BASE,ENTRIES,DATA,BACKENDS,sha

CS,DS,STACK,STOP=0x1000,0x3000,0xf000,0xf800
FIRST,SECOND,FLOAT_INPUT=0x4000,0x4010,0x4020
OPAQUE=bytes.fromhex('123456789abcdef0')
EXPECTED='141329257da52573602e7b5924f4525234cbcf432f412c7ebe5654bdf559c4c8'

class Machine:
 def __init__(self,images):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.u.mem_write(DS*16,b'\xa5'*65536)
  self.images=images
  for a,b,code in images:self.u.mem_write(CS*16+a,code)
  for reg,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_ES,DS),
    (UC_X86_REG_EFLAGS,2)]:self.u.reg_write(reg,value)
  for name in DATA:self.set(name,0)
  self.u.mem_write(DS*16+FIRST,bytes(64));self.u.mem_write(DS*16+FLOAT_INPUT,b'abcdefgh')
  self.raw=[];self.integers=[];self.longs=[];self.truth=[];self.float_inputs=[]
  self.addresses=[];self.float_pointer=FLOAT_INPUT;self.calls=[];self.visited=set()
  self.stop_float=False;self.stopped=False;self.reached=False
  self.u.hook_add(UC_HOOK_CODE,self.on_code);self.u.hook_add(UC_HOOK_INTR,self.interrupt)
 def put(self,o,v):self.u.mem_write(DS*16+o,struct.pack('<H',v&65535))
 def word(self,o):return struct.unpack('<H',self.u.mem_read(DS*16+o,2))[0]
 def set(self,n,v):self.put(DATA[n],v)
 def get(self,n):return self.word(DATA[n])
 def write(self,o,b):self.u.mem_write(DS*16+o,b)
 def read(self,o,n):return bytes(self.u.mem_read(DS*16+o,n))
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16;assert cpu.reg_read(UC_X86_REG_CS)==CS
  if ip==STOP:self.reached=True;cpu.emu_stop();return
  if any(a<=ip<b for a,b,_ in self.images):
   if START<=ip<END:self.visited.add(ip)
   return
  assert ip in BACKENDS,hex(ip)
  name=BACKENDS[ip];sp=cpu.reg_read(UC_X86_REG_SP);arg=self.word(sp+2)
  self.calls.append((name,arg if name.startswith('float_') and name!='float_read' else None))
  cleanup=0;value=0
  if name=='read':assert self.raw;value=self.raw.pop(0)
  elif name=='boolean':assert self.truth;value=self.truth.pop(0)
  elif name=='signed':assert self.longs;value=self.longs.pop(0)
  elif name=='integer':assert self.integers;value=self.integers.pop(0)
  elif name=='long':assert self.longs;value=self.longs.pop(0)
  elif name=='stage':
   assert self.float_inputs;self.write(DATA['float_value'],self.float_inputs.pop(0))
  elif name=='float_read':value=self.float_pointer
  elif name.endswith('_address'):
   value=self.addresses.pop(0) if self.addresses else FIRST
  elif name.startswith('float_'):
   cleanup=2
   if self.stop_float:self.stopped=True;cpu.emu_stop();return
   self.write(DATA['float_value'],OPAQUE)
  else:raise AssertionError(name)
  cpu.reg_write(UC_X86_REG_AX,value&65535);cpu.reg_write(UC_X86_REG_DX,(value>>16)&65535)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def interrupt(self,cpu,number,_):raise AssertionError(f'Unexpected interrupt {number}')
 def invoke(self,name,*args):
  self.reached=self.stopped=False
  self.write(STACK-128,b'\xa5'*144)
  self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=20000)
  if not self.stopped:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd
   assert self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert self.read_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)|(self.u.reg_read(UC_X86_REG_DX)<<16)
 def read_code(self,a,b):return bytes(self.u.mem_read(CS*16+a,b-a))
 def record(self):
  return dict(calls=self.calls,source_type=self.get('source_type'),target_type=self.get('target_type'),
   lookahead=self.get('lookahead'),word_value=self.get('word_value'),dword=self.read(DATA['dword_value'],4).hex(),
   float_value=self.read(DATA['float_value'],8).hex(),destinations=self.read(FIRST,48).hex(),stopped=self.stopped,
   unconsumed=[self.raw,self.integers,self.longs,self.truth,len(self.float_inputs)],
   visited=sorted(self.visited))

def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value

def suite(images):
 records=[];coverage=set();groups={}
 def done(m,group):
  coverage.update(m.visited);groups[group]=groups.get(group,0)+1;records.append(m.record())
 for value in list(range(256))+[0xfffe,0xffff]:
  m=Machine(images);m.raw=[value];m.invoke('metadata');assert m.get('source_type')==value&3 and m.get('target_type')==value>>2;done(m,'metadata')
 for source in range(4):
  for value in [0,1,0x7fff,0x8000,0xffff]:
   m=Machine(images);m.set('source_type',source);m.set('word_value',value);m.write(DATA['dword_value'],struct.pack('<I',0x81230000|value));m.write(DATA['float_value'],b'ABCDEFGH')
   assert m.invoke('word_result')&65535 == (value if source<2 else 0x4241)
   expected=(signed(value,16)&0xffffffff) if source==0 else 0x81230000|value if source==1 else 0x44434241
   assert m.invoke('dword_result')==expected;done(m,'result_coercion')
   m.calls=[];m.invoke('eight_result');assert m.u.reg_read(UC_X86_REG_AX)==DATA['float_value']
   assert m.read(DATA['float_value'],8)==(b'ABCDEFGH' if source==2 else OPAQUE)
   assert m.calls==([] if source==2 else [('float_transform',0x5b)]);done(m,'eight_coercion')
 for source in range(4):
  for target in range(4):
   m=Machine(images);m.set('source_type',source);m.set('target_type',target);m.set('word_value',0x8001)
   m.write(DATA['dword_value'],bytes.fromhex('78563412'));m.write(DATA['float_value'],b'ABCDEFGH')
   m.invoke('store_result')
   if target==0:assert m.word(FIRST)==(0x8001 if source==0 else 0x5678 if source==1 else 0x4241)
   elif target==1:assert m.read(FIRST,4)==(bytes.fromhex('0180ffff') if source==0 else bytes.fromhex('78563412') if source==1 else b'ABCD')
   else:assert m.read(FIRST,8)==(b'ABCDEFGH' if source==2 else OPAQUE)
   done(m,'store_result')
 for target in range(4):
  for value in [0,1,0x8000,0xffff]:
   m=Machine(images);m.set('source_type',3);m.set('target_type',target);m.invoke('store_boolean',value)
   assert m.get('source_type')==0 and m.get('word_value')==value
   if target==0:assert m.word(FIRST)==value
   elif target==1:assert int.from_bytes(m.read(FIRST,4),'little')==signed(value,16)&0xffffffff
   else:assert m.read(FIRST,8)==OPAQUE
   done(m,'store_boolean')
 for name in ['logical_and','logical_or','logical_not']:
  for a in [0,1,0x8000,0xffff]:
   for b in [0,1,0x8000,0xffff]:
    m=Machine(images);m.raw=[0];m.truth=[a] if name=='logical_not' else [a,b]
    m.invoke(name);expected=(not a) if name=='logical_not' else (bool(a) and bool(b)) if name=='logical_and' else (bool(a) or bool(b))
    assert m.word(FIRST)==int(expected);done(m,'logical')
 comparisons=dict(equal=lambda a,b:a==b,less_equal=lambda a,b:a<=b,less=lambda a,b:a<b,
  greater_equal=lambda a,b:a>=b,greater=lambda a,b:a>b,not_equal=lambda a,b:a!=b)
 rng=random.Random(0xa5c02)
 for source,bits,values in [(0,16,[0,1,0x7fff,0x8000,0xffff]),(1,32,[0,1,0x7fff,0x8000,0xffff,0x10000,0x7fffffff,0x80000000,0xffffffff])]:
  pairs=[(a,b) for a in values for b in values]+[(rng.randrange(1<<bits),rng.randrange(1<<bits)) for _ in range(100)]
  for name,predicate in comparisons.items():
   for a,b in pairs:
    m=Machine(images);m.raw=[source]
    if source==0:m.integers=[b,a]
    else:m.longs=[b,a]
    m.invoke(name);assert m.word(FIRST)==int(predicate(signed(a,bits),signed(b,bits)));done(m,'comparisons')
 for name,code in [('equal',0x32),('less_equal',0x48),('less',0x54),('greater_equal',0x68),('greater',0x6d),('not_equal',0x7f)]:
  for source in [2,3]:
   for stops in [False,True]:
    m=Machine(images);m.raw=[source];m.float_inputs=[b'ABCDEFGH'];m.stop_float=stops;m.invoke(name)
    assert ('float_compare',code) in m.calls and m.stopped==stops;done(m,'float_boundary')
 for name,step,code in [('decrement',-1,0x1e),('increment',1,0x5a)]:
  for token in range(256):
   m=Machine(images);m.raw=[token];m.write(FIRST,bytes.fromhex('ffff123456789abc'));m.invoke(name)
   if token%10==1:assert m.word(FIRST)==(0xffff+step)&65535
   elif token%10==2:assert int.from_bytes(m.read(FIRST,4),'little')==(0x3412ffff+step)&0xffffffff
   else:assert m.calls[-1]==('float_destination',code)
   assert m.get('lookahead')==token;done(m,'increment_decrement')
 for source in range(4):
  for target in range(4):
   for chained in [0,1,2]:
    m=Machine(images);m.raw=[(target<<2)|source];m.integers=[0x8001];m.longs=[0x12345678];m.addresses=[FIRST,SECOND]
    m.invoke('assignment',chained)
    if source<3 and target<3:
     if target==0:assert m.word(FIRST)==(0x8001 if source==0 else 0x5678 if source==1 else 0x3412)
     elif target==1:assert m.read(FIRST,4)==(bytes.fromhex('0180ffff') if source==0 else bytes.fromhex('78563412') if source==1 else OPAQUE[:4])
     else:assert m.read(FIRST,8)==(b'abcdefgh' if source==2 else OPAQUE)
     if chained:assert m.read(FIRST,[2,4,8,8][target])==m.read(SECOND,[2,4,8,8][target])
    done(m,'assignment')
 for name in ['assign','assign_chained']:
  m=Machine(images);m.raw=[0];m.integers=[0x8123];m.addresses=[FIRST,SECOND];m.invoke(name)
  assert m.word(FIRST)==0x8123 and m.word(SECOND)==(0x8123 if name=='assign_chained' else 0);done(m,'assignment_wrappers')
 # Actual native memmove sees overlapping source/destination eight-byte ranges.
 for delta in [-3,-1,0,1,3]:
  m=Machine(images);m.raw=[10];m.addresses=[FLOAT_INPUT+delta];before=m.read(FLOAT_INPUT,8);m.invoke('assign')
  assert m.read(FLOAT_INPUT+delta,8)==before;done(m,'overlapping_float_copy')
 for name in ['eight_result','store_result','store_boolean','assign']:
  m=Machine(images);m.stop_float=True;m.set('source_type',0);m.set('target_type',2)
  if name=='assign':m.raw=[8];m.integers=[3]
  m.invoke(name,*([1] if name=='store_boolean' else []));assert m.stopped;done(m,'unavailable_float')
 return records,groups,coverage

def dos_test():
 folder=OUT/('dos-'+str(time.time_ns()));folder.mkdir()
 shutil.copy2(OUT/'OPERATE.EXE',folder/'OPERATE.EXE')
 config=f"""[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{folder}"
c:
OPERATE >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
"""
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 summary=(folder/'DONE.TXT').read_text().strip()
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),(folder/'RESULT.TXT').read_text()
 assert summary.endswith('0 failures'),summary
 return dict(summary=summary,folder=str(folder.relative_to(ROOT)),binary_sha256=sha((folder/'OPERATE.EXE').read_bytes()),
  scope='Linked8086operations/copy; controlled operand/address/classification callbacks; unavailable float services abort the fixture invocation. No floating math or wholeVM.')


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);a=p.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_operations.py')],check=True,stdout=subprocess.DEVNULL)
 binary=(OUT/'operations.bin').read_bytes();assert sha(binary)==EXPECTED and len(binary)==END-START
 predicates=(OUT/'predicates.bin').read_bytes();copy=(OUT/'copy.bin').read_bytes()
 images=[(START,END,binary),(0xdb10,0xdb10+len(predicates),predicates),(0x85b4,0x85b4+len(copy),copy)]
 records,groups,coverage=suite(images)
 assert len(coverage)==464, "Incomplete instruction coverage for pinned native range"
 comparison=None
 if a.original:
  original=a.original.read_bytes();assert sha(original)==SHA
  retained=original[FILE_BASE+START:FILE_BASE+END];assert retained==binary
  native,ng,nc=suite([(START,END,retained),*images[1:]])
  assert native==records and ng==groups and nc==coverage
  comparison=dict(original_sha256=SHA,exact_bytes=True,identical_cpu_records=len(records))
 records_data=(json.dumps(records,sort_keys=True,separators=(",",":"))+"\n").encode()
 (OUT/"cpu-records.json").write_bytes(records_data)
 dos=dos_test()
 report=dict(passed=True,DOS=dos,records_sha256=sha(records_data),cases=len(records),groups=groups,operations_sha256=sha(binary),
  covered_instruction_addresses=sorted(coverage),coverage_count=len(coverage),private_original_comparison=comparison,
  harness_sha256=sha(Path(__file__).read_bytes()),sources=json.loads((OUT/'manifest.json').read_text())['sources'],
  scope='Native operations, classification predicates and overlap-safe copy execute. Operand/address/expression services are explicit fixture queues. Float service uses opaque sentinel return or unavailable-stop policies only; no float mathematics or complete expression VM claim.')
 report['original_inputs']=[] if a.original is None else [str(a.original)]
 report['manifest_sha256']=sha((OUT/'manifest.json').read_bytes())
 (OUT/('cpu-result-native.json' if a.original else 'cpu-result.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['sources','covered_instruction_addresses']},indent=2))

if __name__=='__main__':main()
