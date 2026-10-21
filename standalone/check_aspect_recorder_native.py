#!/usr/bin/env python3
"""Explicit original-instruction recorder probes; never execute analysis EXEs."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_IP,UC_X86_REG_AX,UC_X86_REG_EFLAGS

ROOT=Path(__file__).resolve().parents[1]
DIGEST='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('rx',12,0xdb28,53),('key',12,0xdb5e,80),('tx_flush',12,0xdbae,91),('rx_flush',12,0xdc0a,147),('mode',16,0xe1b4,421)]
CS=0x1000;DS=0x4000;DATA=DS*16;STACK=0xfefe;STOP=0x100


class Probe:
 def __init__(self,binary,overlays):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.calls=[];self.waits=[];self.returned=False;self.unsafe=False;self.halt_at_format=False
  for name,overlay,start,length in UNITS:
   info=overlays[overlay];offset=info['source_file_offset']+start-info['relative_load_segment']*16
   assert 0<=start-info['relative_load_segment']*16 and start+length<=info['relative_end_segment']*16
   self.u.mem_write(CS*16+start,binary[offset:offset+length])
  self.set(0xce00,0x1234);self.u.mem_write(DATA+0x423e,b'   pause 1\r\n   transmit "%s"\r\n\0');self.u.mem_write(DATA+0x425e,b'   waitfor "%s"\r\n\0');self.u.mem_write(DATA+0x25ac,b'endproc\r\n\0')
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def set(self,off,value):self.u.mem_write(DATA+off,struct.pack('<H',value))
 def get(self,off):return struct.unpack('<H',self.u.mem_read(DATA+off,2))[0]
 def string(self,off):
  raw=bytes(self.u.mem_read(DATA+off,200));assert 0 in raw;return raw.split(b'\0',1)[0]
 def hook(self,u,at,size,_):
  if at==CS*16+STOP:self.returned=True;u.emu_stop();return
  if at not in (CS*16+0x9786,CS*16+0x6b72,CS*16+0x8318):return
  sp=u.reg_read(UC_X86_REG_SP);words=struct.unpack('<4H',u.mem_read(DATA+sp,8));cleanup=0
  if at==CS*16+0x9786:
   self.calls.append(dict(handle=words[1],format=words[2],text_hex=self.string(words[3]).hex() if words[2] in (0x423e,0x425e) else None))
   if self.halt_at_format:self.unsafe=True;u.emu_stop();return
  elif at==CS*16+0x6b72:self.waits.append(words[1]);cleanup=2
  else:self.calls.append(dict(close_handle=words[1]))
  u.reg_write(UC_X86_REG_AX,0xffff) # Native ignores modeled CRT failures.
  u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,words[0])
 def call(self,name,arg=None,unsafe=False):
  self.returned=self.unsafe=False;self.halt_at_format=unsafe
  u=self.u;u.mem_write(DATA+STACK-2,b'\xef\xbe'+struct.pack('<H',STOP)+struct.pack('<H',arg or 0)+b'\xa5'*40)
  for register,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xbeef),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,2)]:u.reg_write(register,value)
  start=next(start for n,_,start,_ in UNITS if n==name);u.emu_start(CS*16+start,0,count=100000)
  assert self.returned or self.unsafe,(name,'Instruction budget exhausted')
  if not unsafe:
   for register,value in [(UC_X86_REG_BP,0xbeef),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_SP,STACK+2)]:assert u.reg_read(register)==value,(name,register,u.reg_read(register))
  return bytes(u.mem_read(DATA+STACK-2,44))


def expanded(data):return bytes(v for c in data for v in ([94,c+64] if c<32 else [c]))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',action='store_true',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 source=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';binary=source.read_bytes();assert hashlib.sha256(binary).hexdigest()==DIGEST
 manifest=ROOT/'analysis/pcplus-overlays/manifest.json';r=json.loads(manifest.read_text());assert r['source_sha256']==DIGEST;overlays={i['id']:i for i in r['overlays']};cases=[]
 for size in (0,1,15,16,17,32,60):
  m=Probe(binary,overlays);data=bytes(range(40,40+size))
  for c in data:m.call('rx',c)
  expected=data[-16:];assert m.get(0x373e)==len(expected) and bytes(m.u.mem_read(DATA+0xcd3c,len(expected)))==expected
  cases.append(dict(name='rx_rolling_'+str(size),passed=True,retained_hex=expected.hex()))
 for data in (b'',b'\r\nLogin:',b'\0\r\n',b'\r \nA',b'\r\n   ',b'"^\xff',bytes(range(1,17))):
  m=Probe(binary,overlays);m.set(0x373e,len(data));m.u.mem_write(DATA+0xcd3c,data or b'\0');m.call('rx_flush')
  wanted=bytearray();leading=True;printable=any(c>32 for c in data)
  for c in data:
   if c<32:
    if not c or (printable and leading):continue
    wanted.extend((94,c+64))
   else:wanted.append(c);leading=False
  assert m.calls==[dict(handle=0x1234,format=0x425e,text_hex=bytes(wanted).hex())] and m.get(0x373e)==0
  cases.append(dict(name='rx_prompt_'+data.hex(),passed=True,formatted_hex=bytes(wanted).hex()))
 for data in (b'',b'ABC',b'\r\n',b'"^\xff',b'A'*41,b'\x01'*29):
  m=Probe(binary,overlays);m.set(0x3740,len(data));m.u.mem_write(DATA+0xcd4e,data or b'\0');m.call('tx_flush')
  assert m.calls==[dict(handle=0x1234,format=0x423e,text_hex=expanded(data).hex())] and m.get(0x3740)==0
  cases.append(dict(name='tx_format_'+str(len(data))+'_'+data[:3].hex(),passed=True,formatted_hex=expanded(data).hex()))
 for count in (30,40,41):
  data=b'\x01'*count;m=Probe(binary,overlays);m.set(0x3740,count);m.u.mem_write(DATA+0xcd4e,data)
  after=m.call('tx_flush',unsafe=True);assert m.unsafe and not m.returned and m.calls[0]['text_hex']==expanded(data).hex()
  assert after[:2]!=b'\xef\xbe';cases.append(dict(name='native_stack_overwrite_'+str(count)+'_controls',passed=True,
   emitted_text_bytes=len(expanded(data)),local_buffer_bytes=60,saved_BP_before_hex='efbe',saved_BP_after_hex=after[:2].hex(),stopped_before_damaged_return=True))
 m=Probe(binary,overlays)
 for c in b'\r\nLogin:':m.call('rx',c)
 for key in (0x0041,0x0042,0x0e08,0x0043,0x000d):m.set(0xcffa,key);m.call('key')
 assert m.calls==[dict(handle=0x1234,format=0x425e,text_hex=b'Login:'.hex()),dict(handle=0x1234,format=0x423e,text_hex=b'AC^M'.hex())]
 assert m.waits==[100]*4 and m.get(0x3740)==m.get(0x373e)==0
 cases.append(dict(name='prompt_then_keys_backspace_and_CR',passed=True,calls=m.calls,calibrated_wait_arguments=m.waits))
 m=Probe(binary,overlays);m.set(0xcffa,0x1c0d);m.call('key')
 assert m.calls==[] and m.get(0x3740)==1
 cases.append(dict(name='unstripped_BIOS_CR_word_does_not_flush',passed=True,pending_bytes=1))
 m=Probe(binary,overlays)
 for _ in range(42):m.set(0xcffa,0x1e41);m.call('key')
 assert m.calls==[dict(handle=0x1234,format=0x423e,text_hex=(b'A'*41).hex())] and m.get(0x3740)==1
 cases.append(dict(name='41_raw_bytes_flush_before42nd_key',passed=True,pending_bytes=1))
 for rx,tx in [(0,0),(7,3)]:
  m=Probe(binary,overlays);m.set(0x373c,1);m.set(0x373e,rx);m.set(0x3740,tx);m.u.mem_write(DATA+0xcd4e,b'ABC');m.call('mode')
  assert m.calls==[dict(handle=0x1234,format=0x25ac,text_hex=None),dict(close_handle=0x1234)]
  assert m.get(0x373c)==m.get(0x373e)==m.get(0x3740)==0
  cases.append(dict(name='stop_discards_pending_'+str(rx)+'_'+str(tx),passed=True,calls=m.calls,mode_after=0,mode_ignores_modeled_CRT_failure=True))
 units=[]
 for name,overlay,start,length in UNITS:
  info=overlays[overlay];offset=info['source_file_offset']+start-info['relative_load_segment']*16
  units.append(dict(name=name,overlay=overlay,relative_address=hex(start),file_offset=offset,bytes=length,sha256=hashlib.sha256(binary[offset:offset+length]).hexdigest()))
 result=dict(passed=True,cases=cases,original_cases=len(cases),source_sha256=DIGEST,units=units,
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
  scope='Explicit opt-in replay of verified original instruction ranges under Unicorn with controlled DS=SS, stack and memory CRT/calibrated-wait callbacks. No analysis EXE is executed, no original DOS application/real file/UI/UART/audio run occurs. Three overflow cases stop at the formatting callback before damaged return. Normal cases verify BP/SI/DI, DS/SS and stack return. Observations establish native byte/queue/stop behavior and defects only; maintained recorder, source build/compiler/replay integration and F13 remain unfinished.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'original_cases':len(cases),'native_stack_overwrite_cases':3,'stop_pending_tail_cases':2}))


if __name__=='__main__':main()
