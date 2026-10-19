#!/usr/bin/env python3
"""Execute recovered FIND/CASE with real source CRT/SET/flow instructions.
Near allocation, operand reads and FILE seeks are declared component boundaries.
"""
import argparse
import json
import struct
import subprocess
import re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_find_case import ROOT,OUT,BASELINE,sha
CODE,DATA=0x10000,0x30000

class Machine:
 def __init__(self,manifest):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.u.mem_write(DATA,b'\xa5'*65536);self.ranges=[];self.visited=set()
  for entry in manifest['units']+manifest['helpers']:
   blob=(OUT/entry['file']).read_bytes();self.u.mem_write(CODE+entry['start'],blob)
   self.ranges.append((entry['start'],entry['end']))
  self.tokens=[];self.strings=[];self.integer=0;self.option=0;self.destination=0x4200
  self.target=0x12345678;self.seeks=[];self.seek_result=0;self.trace=[]
  self.allocations=[];self.requests=[];self.freed=[];self.fail_at=0;self.fail_stop=False;self.stopped=None
  self.put(0xe38e,0);self.put(0xe392,0);self.put(0xe394,0)
  for reg,value in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:self.u.reg_write(reg,value)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
  self.u.hook_add(UC_HOOK_INTR,lambda *args:(_ for _ in ()).throw(AssertionError('Unexpected interrupt')))
 def get(self,offset):return struct.unpack('<H',self.u.mem_read(DATA+offset,2))[0]
 def put(self,offset,value):self.u.mem_write(DATA+offset,struct.pack('<H',value&65535))
 def arg(self,n):return self.get(self.u.reg_read(UC_X86_REG_SP)+2+n*2)
 def text(self,offset):
  result=bytes(self.u.mem_read(DATA+offset,min(81,65536-offset))).split(b'\0',1)
  assert len(result)==2,('unterminated fixture',hex(offset))
  return result[0]
 def string(self,offset,value):assert len(value)<=80;self.u.mem_write(DATA+offset,value+b'\0')
 def returned(self,value=0,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,value&65535)
  self.u.reg_write(UC_X86_REG_IP,self.get(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xf000:u.emu_stop();return
  if ip==0xcdef:u.reg_write(UC_X86_REG_IP,0xdcdb);return # declared overlay thunk
  if ip==0x9128 and self.arg(0)==0:
   self.stopped='native-uppercase-NULL';u.emu_stop();return
  if ip in [0xce1f,0xdf04]:
   assert self.strings;self.trace.append('string');self.returned(self.strings.pop(0));return
  if ip==0xcd5f:self.trace.append('option');self.returned(self.option);return
  if ip==0xce13:self.trace.append('destination');self.returned(self.destination);return
  if ip==0x4cb4:
   assert self.tokens;self.trace.append('byte');self.returned(self.tokens.pop(0));return
  if ip==0xdc48:self.trace.append('integer');self.returned(self.integer);return
  if ip==0xe176:
   self.trace.append('DWORD');u.reg_write(UC_X86_REG_DX,self.target>>16);self.returned(self.target);return
  if ip==0xd287:
   self.trace.append('seek');self.seeks.append(self.arg(0)|(self.arg(1)<<16));self.returned(self.seek_result,4);return
  if ip==0x92a8:
   size=self.arg(0);assert 1<=size<=81,size;self.requests.append(size)
   if len(self.requests)==self.fail_at:
    if self.fail_stop:self.stopped='allocator-model-stop';u.emu_stop();return
    self.returned(0);return
   pointer=0x5000+len(self.allocations)*0x100;assert len(self.allocations)<2
   self.allocations.append((pointer,size));self.returned(pointer);return
  if ip==0x92a4:
   pointer=self.arg(0);assert pointer in [p for p,n in self.allocations] and pointer not in self.freed
   self.freed.append(pointer);self.returned();return
  assert any(start<=ip<end for start,end in self.ranges),hex(ip)
  self.visited.add(ip)
 def run(self,entry,args=(),callee_cleanup=0):
  for reg,value in [(UC_X86_REG_BP,0x8700),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x4321),(UC_X86_REG_SP,0x8800),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(reg,value)
  self.put(0x8800,0xf000)
  for i,value in enumerate(args):self.put(0x8802+i*2,value)
  self.u.emu_start(CODE+entry,CODE+65535,count=30000)
  if not self.stopped:
   assert self.u.reg_read(UC_X86_REG_IP)==0xf000
   assert self.u.reg_read(UC_X86_REG_SP)==0x8802+callee_cleanup
   assert self.u.reg_read(UC_X86_REG_BP)==0x8700 and self.u.reg_read(UC_X86_REG_SI)==0x1234 and self.u.reg_read(UC_X86_REG_DI)==0x5678
   assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
   assert self.u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
  return self.u.reg_read(UC_X86_REG_AX)
 def setting(self,find,value):self.tokens=[value];self.run(0xea1c if find else 0xec77)

class Lifecycle(Machine):
 """Actual native dispatcher; loader/UI/handler callbacks are explicit models."""
 def __init__(self,manifest):
  super().__init__(manifest);self.initialized=0;self.opens=0;self.open_flags=[];self.cleanups=[]
  for slot in range(215):self.put(0x4b08+slot*2,0xf100)
  self.put(0xe104,0x7000)
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xc1d7:
   self.initialized+=1;self.put(0xe392,0);self.put(0xe394,0);self.returned();return
  if ip==0xc21f:
   self.opens+=1;self.open_flags.append((self.get(0xe392),self.get(0xe394)))
   for field in [0xe378,0xe382,0xe2f8,0x8e20]:self.put(field,0)
   self.put(0x4b02,0x7000);self.returned(1,4);return
  if ip==0x9048:self.returned();return
  if ip==0x4de9:self.returned();return
  if ip==0x4cb4:self.returned();return
  if ip==0xf100:
   if self.opens%2:self.put(0xe392,17);self.put(0xe394,19);self.put(0xe378,999)
   else:self.put(0xe378,1)
   self.returned();return
  if ip in [0xc2eb,0xc273,0x8318,0x4bff]:
   self.cleanups.append((ip,self.get(0xe392),self.get(0xe394)));self.returned();return
  super().hook(u,address,size,user)


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 manifest_path=OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
 assert manifest['original_inputs']==[] and manifest['native_bytes']==401
 for path,digest in manifest['sources'].items():assert sha(ROOT/path)==digest,path
 for entry in manifest['units']+manifest['helpers']:assert sha(OUT/entry['file'])==entry['sha256']
 for leaf,digest in manifest['objects'].items():assert sha(OUT/leaf)==digest
 results=[];visited=set()
 def done(machine,category):
  visited.update(machine.visited);results.append(category)
 # Every raw SET byte is used by the actual native consumer, not a shadow flag.
 patterns=[(b'AbCdE',b'bc'),(b'aaaaab',b'aaab'),(b'',b''),(b'',b'A'),(b'abc',b''),(b'abc',b'abcdef'),(b'\x80aZ',b'\x80Az'),(b'A'*80,b'A'*80),(b'abc',b'z')]
 for flag in range(256):
  for hay,needle in patterns:
   m=Machine(manifest);m.setting(True,flag);m.option=flag%2;m.string(0x3000,hay);m.string(0x3100,needle);m.strings=[0x3000,0x3100]
   m.run(0x4fb4);index=(hay if flag else hay.upper()).find(needle if flag else needle.upper())
   assert m.get(0xe39c)==int(index>=0)
   assert m.get(m.destination)==((index if index>=0 else -0x3000)&65535 if m.option else 0xa5a5)
   assert m.text(0x3000)==hay and m.text(0x3100)==needle and not m.strings
   assert len(m.allocations)==len(m.freed)==(0 if flag else 2)
   if not flag:assert m.requests==[len(hay)+1,len(needle)+1]
   done(m,'FIND raw SET byte/case/index/input/near-owner')
 for flag in [0,1,255]:
  m=Machine(manifest);m.setting(True,flag);m.option=1;m.string(0xff20,b'ABC');m.string(0x3100,b'Z');m.strings=[0xff20,0x3100];m.run(0x4fb4)
  assert m.get(m.destination)==0xe0 and m.get(0xe39c)==0;done(m,'FIND wrapped absent-index')
 for fail_at in [1,2]:
  for stop in [False,True]:
   m=Machine(manifest);m.fail_at=fail_at;m.fail_stop=stop;m.string(0x3000,b'AbC');m.string(0x3100,b'b');m.strings=[0x3000,0x3100];m.run(0x4fb4)
   assert m.stopped==('allocator-model-stop' if stop else 'native-uppercase-NULL')
   assert not m.freed # No invented rollback on either declared failure boundary.
   done(m,'allocation-return-NULL' if not stop else 'allocator-explicit-stop-model')
 for flag in range(256):
  m=Machine(manifest);m.setting(False,flag);m.tokens=[140];m.string(0x3000,b'AbC');m.strings=[0x3000];m.run(0xd372)
  assert m.text(0xe322)==b'AbC' and m.get(0xe38c)==140 and bytes(m.u.mem_read(DATA+0xe376,1))==b'\0'
  assert m.seeks==[m.target] and m.trace[-2:]==['DWORD','seek']
  m.seeks=[];m.string(0x3100,b'abc');m.strings=[0x3100];m.run(0xd39f)
  assert m.seeks==([] if not flag else [m.target]);assert not m.strings
  done(m,'SWITCH/CASE raw SET byte/string match/32bit seek')
 for token in [141,142,65535]:
  for flag in [0,1,255]:
   for value in [0,0x7fff,0x8000,0xffff]:
    for match in [True,False]:
     m=Machine(manifest);m.setting(False,flag);m.tokens=[token];m.integer=value;m.run(0xd372)
     assert m.get(0xe374)==value and bytes(m.u.mem_read(DATA+0xe376,1))[0]==((token if token<32768 else token-65536)%10 if token<32768 else 255)
     m.seeks=[];m.integer=value if match else value^1;m.target=0xffffffff;m.seek_result=0xffff;m.run(0xd39f)
     assert m.seeks==([] if match else [0xffffffff]);done(m,'numeric CASE ignores sensitivity/native token/unchecked failed seek')
 m=Machine(manifest)
 for text in [b'FIRST',b'SECOND']:
  m.tokens=[140];m.string(0x3000,text);m.strings=[0x3000];m.run(0xd372)
 m.seeks=[];m.string(0x3100,b'FIRST');m.strings=[0x3100];m.run(0xd39f)
 assert m.text(0xe322)==b'SECOND' and m.seeks==[m.target];done(m,'shared SWITCH state is not a nested-state stack')
 m=Lifecycle(manifest);m.run(0x4b1f,[1,0x7000],4)
 assert m.initialized==1 and m.open_flags==[(0,0),(17,19)] and m.get(0xe392)==17 and m.get(0xe394)==19
 done(m,'actual dispatcher initializes once and preserves flags across CHAIN restart; loader boundaries modeled')
 m.opens=0;m.open_flags=[];m.run(0x4b1f,[1,0x7000],4)
 assert m.initialized==2 and m.open_flags==[(0,0),(17,19)]
 done(m,'fresh dispatcher invocation repeats modeled native defaults')
 original_inputs=[]
 if args.original:
  baseline=json.loads(BASELINE.read_text());assert sha(args.original)==baseline['original_sha256'];blob=args.original.read_bytes()
  for unit in manifest['units']:assert blob[unit['file_offset']:unit['file_offset']+unit['length']]==(OUT/unit['file']).read_bytes()
  original_inputs=[dict(sha256=sha(args.original),scope='Optional static exact401-byte source comparison only; never execute original.')]
 expected_units=[]
 for unit in manifest['units']:
  text=subprocess.check_output(['ndisasm','-b16','-o'+hex(unit['start']),str(OUT/unit['file'])],text=True)
  addresses={int(line.split()[0],16) for line in text.splitlines() if re.match(r'^[0-9A-Fa-f]{8}\s',line)}
  assert addresses<=visited,(unit['module'],unit['unit'],sorted(addresses-visited))
  expected_units.append(dict(module=unit['module'],unit=unit['unit'],instructions=len(addresses),all_instructions_visited=True))
 counts={name:results.count(name) for name in sorted(set(results))}
 report=dict(passed=True,cases=len(results),counts=counts,visited_instruction_addresses=len(visited),
             native_unit_coverage=expected_units,
             manifest_sha256=sha(manifest_path),checker_sha256=sha(Path(__file__)),original_inputs=original_inputs,
             scope='Actual401nativebytes with real source CRT/SET/flow/dispatcher underCPU, DS=SS cdecl. Operand/FILE/near-allocator/loader/UI boundaries explicit; no DOS product integration or complete FIND/SWITCH compiler claim.',
             limitations=['Original allocation failure reaches unchecked uppercase(NULL); test stops before dereference, separate allocator-stop model is not native rollback.',
                          'Native D6EA reset values and call placement are retained REA evidence; lifecycle CPU executes dispatcher with a modeled initializer, open/cleanup and handler boundaries.',
                          'Shared SWITCH globals do not prove complete nested SWITCH compiler semantics; malformed tokens/indices/seek remain unchecked native behavior.'])
 (OUT/('checks-original.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n')
 print('FIND/CASE:',len(results),'CPU cases',len(visited),'instruction addresses PASS')

if __name__=='__main__':main()
