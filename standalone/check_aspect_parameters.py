#!/usr/bin/env python3
"""Native typed parameter CPU/DOS checks with actual numeric/flow/stack/copy.

Float and string services return opaque8/81-byte fixture buffers or stop. This
observes routing/copy behavior, never claims that arbitrary tokens are valid
floating operands or that modeled buffers implement the real string parser.
Optional original input is isolated behind --original.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_IP,UC_X86_REG_EFLAGS)
from check_aspect_operands import Machine as OperandMachine,CS,DS,STACK,STOP,BANK_A,BANK_B,LONG_BANK,SYSTEM,LOOKAHEAD
from build_aspect_flow import BASE,LENGTH,FILE_BASE,STACK_START,STACK_END,COPY,COPY_END,UNITS as FLOW_UNITS
from build_aspect_operands import UNITS as OPER_UNITS
from build_aspect_parameters import ROOT,OUT,START,END,FILE_START,SHA,ENTRIES,sha

EXPECTED='95dd7e90c84588a2a71ed957a068309103deeb7840fe66359e62768e6c1cd65a'
FLOAT,STRING=0x6000,0x6100
OPAQUE_FLOAT=bytes((i*73)&255 for i in range(8))
OPAQUE_STRING=bytes((i*29)&255 for i in range(81))


class Machine(OperandMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.u.mem_write(DS*16+FLOAT,OPAQUE_FLOAT);self.u.mem_write(DS*16+STRING,OPAQUE_STRING)
  self.service_available=True;self.float_tokens=[];self.string_reads=0;self.parameter_visits=set()
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if START<=ip<END:self.parameter_visits.add(ip)
  if ip not in (0xdd26,0xdf04):return super().on_code(cpu,address,size,_)
  if not self.service_available:self.aborted=True;cpu.emu_stop();return
  if ip==0xdd26:
   self.float_tokens.append(self.word(LOOKAHEAD));self.put(LOOKAHEAD,0);value=FLOAT
  else:self.string_reads+=1;value=STRING
  sp=cpu.reg_read(UC_X86_REG_SP);cpu.reg_write(UC_X86_REG_AX,value)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2)
 def invoke(self,name):
  self.reached=self.aborted=False
  self.u.mem_write(DS*16+STACK-128,b'\xa5'*144);self.put(STACK,STOP)
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=100000)
  if not self.aborted:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd
   assert self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert bytes(self.u.mem_read(CS*16+a,b-a))==code
  return self.u.reg_read(UC_X86_REG_AX)
 def record(self):
  result=super().record();result.update(float_tokens=self.float_tokens,string_reads=self.string_reads,parameter_visits=sorted(self.parameter_visits));return result


def suite(images):
 records=[];coverage=set();groups={}
 def done(m,group):records.append(m.record());coverage.update(m.parameter_visits);groups[group]=groups.get(group,0)+1
 def pushed(m,expected,pointer=BASE):
  assert not m.aborted and not m.errors
  assert m.get('stack_pointer')==(pointer+len(expected))&65535
  assert bytes(m.u.mem_read(DS*16+pointer,len(expected)))==expected
  assert m.word(LOOKAHEAD)==0
 selectors=[(101,2,1,BANK_A),(141,2,1,BANK_B),(121,2,3,SYSTEM),(111,2,None,None),
            (151,2,None,None),(161,2,None,None),(171,2,None,None),(181,2,None,None),
            (112,4,None,None),(122,4,3,SYSTEM),(142,4,2,LONG_BANK),(152,4,None,None),
            (162,4,None,None),(172,4,None,None)]
 for token,width,shift,bank in selectors:
  for index in range(256):
   if token in (151,161,152,162):payload=index.to_bytes(2,'little')
   elif token==171:payload=(index*257^0x1234).to_bytes(2,'little')
   elif token==172:payload=(0x89abcdef^(index*0x01010101)).to_bytes(4,'little')
   else:payload=bytes([index])
   m=Machine(images,bytes([token])+payload);m.set('frame',0x6400)
   m.u.mem_write(DS*16+0x6300,bytes((i*37+11)&255 for i in range(768)))
   if bank is not None:
    address=(bank+(index<<shift))&65535;value=m.word(address) if width==2 else m.long(address)
   elif token in (111,112):value=(index^0x7654) if width==2 else (0x89abcdef^index)
   elif token in (151,161,152,162):
    address=(0x6400+(-index if token in (151,152) else index))&65535;value=m.word(address) if width==2 else m.long(address)
   elif token in (171,172):value=int.from_bytes(payload,'little')
   else:value=index
   m.invoke('push_numeric');pushed(m,value.to_bytes(width,'little'));done(m,'numeric_selection')
 valid_int=(101,111,121,141,151,161,171,181);valid_long=(112,122,142,152,162,172)
 for token in range(256):
  if token in valid_int or token in valid_long:continue
  m=Machine(images,bytes([token]));m.invoke('push_numeric')
  if token%10==1:pushed(m,b'\xdd\xcc');assert m.invalids==1
  elif token%10==2:pushed(m,b'\xdd\xcc\xbb\xaa');assert m.invalids==1
  else:pushed(m,OPAQUE_FLOAT);assert m.float_tokens==[token]
  done(m,'classification_fallthrough')
 m=Machine(images);m.invoke('push_numeric');pushed(m,OPAQUE_FLOAT);assert m.float_tokens==[65535];done(m,'EOF_forwarding')
 for offset in range(32):
  m=Machine(images);m.set('stack_pointer',BASE+offset);m.invoke('push_string');pushed(m,OPAQUE_STRING,BASE+offset)
  assert m.string_reads==1 and m.position()==0;done(m,'string_copy')
 for pointer in (0,1,BASE,BASE+LENGTH,0xffff):
  for offset in (0,1,2,81,65535):
   m=Machine(images,offset.to_bytes(2,'little'));m.set('stack_pointer',pointer)
   assert m.invoke('stack_address')==(pointer+offset)&65535 and m.get('stack_pointer')==pointer and not m.errors;done(m,'unchecked_address')
 m=Machine(images);m.set('stack_pointer',BASE);assert m.invoke('stack_address')==(BASE-1)&65535;done(m,'EOF_address')
 shapes=[('push_numeric',b'\xb5\x34',b'\x34\0'),('push_numeric',b'\xac\x34\x12\x78\x56',bytes.fromhex('34127856')),
         ('push_numeric',b'\x7b',OPAQUE_FLOAT),('push_string',b'',OPAQUE_STRING)]
 for name,data,expected in shapes:
  width=len(expected)
  for returns in (False,True):
   m=Machine(images,data);pointer=BASE+LENGTH-width+1;m.set('stack_pointer',pointer);m.error_returns=returns
   m.invoke(name);assert m.errors==1 and m.aborted==(not returns)
   assert m.get('stack_pointer')==pointer+(width if returns else 0) and m.position()==len(data)
   assert bytes(m.u.mem_read(DS*16+pointer,width))==(expected if returns else b'\xa5'*width);done(m,'reserve_failure')
  m=Machine(images,data);pointer=65536-width;m.set('stack_pointer',pointer);m.invoke(name)
  pushed(m,expected,pointer);done(m,'unchecked_pointer_wrap')
 for token in (1,2):
  m=Machine(images,bytes([token]));m.invalid_returns=False;m.invoke('push_numeric')
  assert m.aborted and m.get('stack_pointer')==BASE and not m.errors;done(m,'operand_abort')
 for name,data in [('push_numeric',b'\x7b'),('push_string',b'')]:
  m=Machine(images,data);m.service_available=False;m.invoke(name)
  assert m.aborted and m.get('stack_pointer')==BASE and not m.errors;done(m,'unavailable_reader')
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
PARAM >RESULT.TXT
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
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 summary=(OUT/'DONE.TXT').read_text().strip()
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 assert summary.endswith('0 failures'),summary
 return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_parameters.py')],check=True)
 code=(OUT/'parameters.bin').read_bytes();assert sha(code)==EXPECTED
 images=[(START,END,code)]
 for prefix,units in [('operand-',OPER_UNITS),('flow-',FLOW_UNITS)]:
  for _,name,a,b in units:images.append((a,b,(OUT/(prefix+name+'.bin')).read_bytes()))
 images.extend([(STACK_START,STACK_END,(OUT/'stack.bin').read_bytes()),(COPY,COPY_END,(OUT/'copy.bin').read_bytes())])
 records,groups,coverage=suite(images);optional=None
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for a,b,code_ in images:
   offset=0x1200+a if a==COPY else FILE_BASE+a;raw=original[offset:offset+b-a];assert raw==code_;native.append((a,b,raw))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,source_file_start=FILE_START,source_file_end_exclusive=FILE_START+END-START,exact_parameter_bytes=END-START,paired_cpu_scenarios=len(records))
 summary=dos_test()
 report=dict(passed=True,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'PARAM.EXE').read_bytes()),flat_sha256=sha(code),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256=sha((ROOT/'standalone/check_aspect_operands.py').read_bytes()),original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Three native parameter entries plus actual numeric operand/flow/typed stack/copy. Opaque8/81-byte reader policies and error-return/stop only. Noninteger/nonlong andEOF routing do not establish float parser acceptance; zero lookahead retains absent sentinel semantics. No rollback, safe stack or complete VM claim.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
