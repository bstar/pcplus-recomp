#!/usr/bin/env python3
"""Recovered overlay17 arithmetic CPU/8086 DOS component checks.

Numeric metadata/load/store and copy instructions execute unchanged. Controlled
long-helper callbacks validate caller arguments and model bounded integer work;
this does not prove native resident helper behavior. Float services stop as
unavailable, without approximating float arithmetic. Optional original inputs
are isolated behind --original. Unicorn uses later-x86 CL masking; full8086
word-shift counts are checked separately by DOSBox-X's8086 core.
"""
import argparse
import json
import os
from pathlib import Path
import random
import struct
import subprocess
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_IP,UC_X86_REG_EFLAGS)
from check_aspect_operations import Machine as OpsMachine,CS,DS,STACK,STOP,FIRST,DATA,signed
from build_aspect_operations import START as OPS_START,END as OPS_END,FILE_BASE as OPS_FILE_BASE
from build_aspect_arithmetic import ROOT,OUT,START,END,FILE_BASE,SHA,ENTRIES,LONG_BACKENDS,sha

EXPECTED='c9e9a5eb59f5fc5f2ffe56ff9dade5e8225d55ebda8a94a80f1a1b7620e3d19f'
STAGE_TYPES,FLOAT_ZERO=0xe146,0xe128


def truncdiv(a,b):return (abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)


class Machine(OpsMachine):
 def __init__(self,images):
  super().__init__(images)
  self.stop_float=True;self.error_returns=True;self.error_codes=[];self.stage_index=0
  self.stage_tokens=[123,123];self.arith_visited=set();self.helper_calls=[];self.trap=None
  self.write(FLOAT_ZERO,bytes(8));self.write(STAGE_TYPES,bytes(2))
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if START<=ip<END:self.arith_visited.add(ip)
  if ip not in LONG_BACKENDS and ip not in (0x4efb,0x9ac0,0xdbdd):
   return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);args=[self.word(sp+i) for i in (2,4,6)]
  cleanup=0;value=0
  if ip in LONG_BACKENDS:
   name=LONG_BACKENDS[ip];pointer,low,high=args
   assert pointer==DATA['dword_value']
   left=int.from_bytes(self.read(pointer,4),'little');right=low|(high<<16)
   if name.startswith('shift_'):right=low&255;cleanup=4
   else:cleanup=6
   if name=='multiply':result=left*right
   elif name=='shift_left':result=left<<right
   elif name=='shift_right':result=signed(left,32)>>right
   else:
    a,b=signed(left,32),signed(right,32);assert b and not(a==-0x80000000 and b==-1)
    q=truncdiv(a,b);result=q if name=='divide' else a-q*b
   self.helper_calls.append(dict(name=name,left=left,right=right))
   self.write(pointer,(result&0xffffffff).to_bytes(4,'little'))
  elif ip==0x4efb:
   assert args[0]==2;self.error_codes.append(2);cleanup=2
   if not self.error_returns:self.stopped=True;cpu.emu_stop();return
  elif ip==0x9ac0:
   a,b,n=args;assert n==8
   left,right=self.read(a,n),self.read(b,n);value=65535 if left<right else int(left>right);self.calls.append(('byte_compare',None))
  else:
   assert self.float_inputs and self.stage_index<2
   self.write(DATA['float_value']+self.stage_index*8,self.float_inputs.pop(0))
   self.write(STAGE_TYPES+self.stage_index,bytes([self.stage_tokens[self.stage_index]]))
   self.stage_index+=1;self.calls.append(('stage',None))
  cpu.reg_write(UC_X86_REG_AX,value&65535);cpu.reg_write(UC_X86_REG_DX,value>>16)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def interrupt(self,cpu,number,_):
  assert number==0,'Unexpected interrupt'
  self.trap=0;self.stopped=True;cpu.emu_stop()
 def invoke(self,name,*args):
  self.reached=self.stopped=False
  self.write(STACK-128,b'\xa5'*144);self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=30000)
  if not self.stopped:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd
   assert self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert self.read_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)|(self.u.reg_read(UC_X86_REG_DX)<<16)
 def record(self):
  result=super().record();result.update(error_codes=self.error_codes,helper_calls=self.helper_calls,trap=self.trap,arith_visited=sorted(self.arith_visited));return result


def expected(name,a,b,bits):
 mask=(1<<bits)-1
 if name=='add':v=a+b
 elif name=='subtract':v=a-b
 elif name=='multiply':v=a*b
 elif name=='bit_and':v=a&b
 elif name=='bit_or':v=a|b
 elif name=='bit_xor':v=a^b
 elif name=='bit_not':v=~a
 elif name=='negate':v=-a
 elif name=='shift_left':v=a<<b
 elif name=='shift_right':v=signed(a,bits)>>b
 else:
  sa,sb=signed(a,bits),signed(b,bits);q=truncdiv(sa,sb);v=q if name=='divide' else sa-q*sb
 return v&mask


def suite(images):
 records=[];coverage=set();groups={}
 def done(m,group):
  records.append(m.record());coverage.update(m.arith_visited);groups[group]=groups.get(group,0)+1
 names=['add','subtract','multiply','bit_and','bit_or','bit_xor','bit_not','negate','shift_left','shift_right','divide','modulo']
 rng=random.Random(0xa5c17)
 for source,bits,values in [(0,16,[0,1,2,0x7fff,0x8000,0xffff]),(1,32,[0,1,2,0xffff,0x10000,0x7fffffff,0x80000000,0xffffffff])]:
  for name in names:
   pairs=[(a,b) for a in values for b in ([0,1,2,15,16,17,31] if name.startswith('shift') else values)]
   if not name.startswith('shift'):pairs += [(rng.randrange(1<<bits),rng.randrange(1<<bits)) for _ in range(32)]
   for a,b in pairs:
    if name in ('divide','modulo') and (not b or (a==1<<(bits-1) and b==(1<<bits)-1)):continue
    for target in (0,1):
     m=Machine(images);m.raw=[(target<<2)|source]
     if source==0:m.integers=[a,b]
     else:m.longs=[a,b]
     m.invoke(name);value=expected(name,a,b,bits)
     want=(value&65535) if target==0 else (signed(value,16)&0xffffffff) if source==0 else value
     assert int.from_bytes(m.read(FIRST,2 if target==0 else 4),'little')==want,(source,name,hex(a),hex(b),hex(want),m.record())
     assert not m.stopped and not m.error_codes;done(m,'word' if source==0 else 'long_callback')
 for name in ('divide','modulo'):
  m=Machine(images);m.raw=[0];m.integers=[0x8000,0xffff];m.invoke(name)
  assert m.trap==0 and not m.error_codes and m.read(FIRST,4)==bytes(4);done(m,'word_INT0')
  for source in (0,1):
   for returns in (False,True):
    m=Machine(images);m.raw=[source];m.integers=[13,0];m.longs=[13,0];m.truth=[1];m.error_returns=returns;m.invoke(name)
    assert m.error_codes==[2] and m.stopped==(not returns) and len(m.truth)==int(not returns)
    assert m.read(FIRST,4)==bytes(4);done(m,'zero_divisor')
 for operation in (0,0x26,0x7b,0xffff):
  m=Machine(images);m.raw=[0];m.integers=[17,3];m.invoke('division',operation)
  assert m.word(FIRST)==(5 if operation==0x26 else 2);done(m,'division_operation')
 for returns in (False,True):
  m=Machine(images);m.truth=[0x8000];m.error_returns=returns;value=m.invoke('zero_divisor')
  assert m.error_codes==[2] and m.stopped==(not returns)
  if returns:assert value&65535==1 and not m.truth
  done(m,'zero_helper')
 for name,code in [('add',0),('subtract',0xb5),('multiply',0x7d),('negate',0x7e)]:
  for source in (2,3):
   m=Machine(images);m.raw=[source];m.float_inputs=[b'ABCDEFGH'];m.invoke(name)
   assert m.stopped and any(call==('float_transform' if name=='negate' else 'float_operand',code) for call in m.calls);done(m,'float_unavailable')
 for name,code in [('divide',0x26),('modulo',0x7b)]:
  for token in (121,122,123):
   for zero in (False,True):
    for returns in (False,True):
     m=Machine(images);m.raw=[2];m.stage_tokens=[123,token]
     second=bytes(8) if zero else bytes.fromhex('0100000000000000')
     m.float_inputs=[b'ABCDEFGH',second];m.truth=[1];m.error_returns=returns;m.invoke(name)
     if zero:
      assert m.error_codes==[2] and m.stopped==(not returns) and len(m.truth)==int(not returns)
     else:assert m.stopped and ('float_transform',code) in m.calls
     assert m.read(FIRST,8)==bytes(8);done(m,'staged_zero_test')
 # Source type2/3 bitwise/shift paths intentionally use signed-long callbacks,
 # mutate the dword work value, then store opaque float bytes without FP math.
 for source in (2,3):
  for name in ('bit_and','bit_or','bit_xor','bit_not','shift_left','shift_right'):
   m=Machine(images);m.raw=[source];m.write(DATA['float_value'],b'ABCDEFGH');m.float_inputs=[b'ABCDEFGH'];m.longs=[1];m.invoke(name)
   assert m.word(FIRST)==0x4241 and not m.stopped;done(m,'type_fallthrough')
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
ARITH >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip()
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 assert summary.endswith('0 failures'),summary
 return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_arithmetic.py')],check=True)
 code=(OUT/'arithmetic.bin').read_bytes();assert sha(code)==EXPECTED
 images=[(START,END,code),(OPS_START,OPS_END,(OUT/'operations.bin').read_bytes()),
  (0xdb10,0xdb65,(OUT/'predicates.bin').read_bytes()),(0x85b4,0x85fc,(OUT/'copy.bin').read_bytes())]
 records,groups,coverage=suite(images);optional=None
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for a,b,code_ in images:
   offset=(FILE_BASE if a==START else 0x1200 if a==0x85b4 else OPS_FILE_BASE)+a
   raw=original[offset:offset+b-a];assert raw==code_;native.append((a,b,raw))
  old,oldgroups,oldcoverage=suite(native);assert (old,oldgroups,oldcoverage)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,source_file_start=FILE_BASE+START,source_file_end_exclusive=FILE_BASE+END,exact_arithmetic_bytes=END-START,paired_cpu_scenarios=len(records))
 summary=dos_test()
 report=dict(passed=True,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'ARITH.EXE').read_bytes()),flat_sha256=sha(code),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256=sha((ROOT/'standalone/check_aspect_operations.py').read_bytes()),
  original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='14native arithmetic entries and numeric metadata/load/store/copy. Controlled long helpers, operands, float availability and error policies; native resident long services and full VM unproven. CPUword-shift math onlycounts0..31; DOS8086checksall0..255. WordMIN/-1 trapsINT0 preserved; no floating approximation.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
