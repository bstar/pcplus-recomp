#!/usr/bin/env python3
"""Check native serial commands with explicit device/time component callbacks.

No UART, modem or flowcontrol acceptance is claimed by this unit diagnostic.
--original separately checks pinned bytes and consumed ctype predicate data.
"""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_console import Machine as BaseMachine,decode
from check_aspect_strings import CS,DS,STACK,STOP,DATA,BUILTIN
from build_aspect_serial_commands import ROOT,OUT,SHA,ENTRIES,sha

EXPECTED=['c7aa9f633639f4f58d7a9ed02dcbe42421749d391a53d2b103671b9ab83dce8a', 'bed1126fc9c04693d383651c2944f457ac59a79d8f5a765082ae208991c7af5f', 'e007929f4330589b441dd73a6e2c1356e470a269d9a1f1c7dd2650620deb1fbb', 'c982a9bf143167f6f6b8ba5177de7ed3b4baf03b759b4fb2ae81c5e9082cd21e', '79bbff0db21dc51fb52bc4fec0ff85008468d10eb5a812ad9eb6a49e1f6bf65c', '09e8a1c0bff77a5fc8498f60f72883f846bfbb34d4a56e546d369b9497d85c93', '52cdd99778c6ef200999d51f0f8d100d64939f480518d9e5abf6f1fb532f5a4d']
CASE,RESULT,RXCOUNT,CTYPE,PAUSE,ECHO,DELAY=0xe396,0xe39a,0x8e20,0x7caf,0x1d66,0x1d1a,0x1d68
DAY=0x1800b0
PATTERNS=[b'',b'A',b'AB',b'AAB',b'ABAB',b'NO CARRIER',b'login:',b'^@',b'^M^J',b'^^^']
STREAMS=[b'',b'A',b'aaab',b'ABABAB',b'AAAAB',b'xxNO CARRIERyy',b'Login:',b'abABab',b'xyz',b'^']
def literal(value):return b'\xab'+struct.pack('<H',value&65535)
def timeout(value=None):return b'\0' if value is None else b'\1\x1a' if not value else b'\1'+literal(value)
def signed(v):return v-0x100000000 if v&0x80000000 else v
def expired(count,start,now):
 end=(start+count*18)&0xffffffff;wrap=signed(end)>DAY
 if wrap:end=(end-DAY)&0xffffffff
 return (signed(now)<signed(start) and signed(now)>=signed(end)) if wrap else (signed(now)>=signed(end) or signed(now)<signed(start))
def match(pattern,data,sensitive):
 if not sensitive:pattern=pattern.upper();data=data.upper()
 p=0
 for i,c in enumerate(data):
  if p<len(pattern) and pattern[p]==c:p+=1
  else:p=int(bool(pattern) and pattern[0]==c)
  if p==len(pattern):return True,i+1
 return not pattern,len(data)


class Machine(BaseMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.put(CASE,0);self.put(RESULT,0);self.put(RXCOUNT,0);self.put(ECHO,0);self.put(DELAY,0)
  self.write(PAUSE,b'~');self.write(CTYPE,bytes(2 if 97<=i<=122 else 0 for i in range(256)))
  self.rx=b'';self.rx_head=0;self.tx=[];self.pauses=[];self.delays=[];self.serial_visits=set()
  self.clock_values=[0];self.clock_reads=0;self.cancel_after=1;self.arrivals=[]
 def queued(self,data):self.rx=bytes(data);self.rx_head=0;self.put(RXCOUNT,len(data))
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if any(a<=ip<b for a,b in [(0x5176,0x517f),(0x5188,0x52d0),(0x48cc,0x4934),(0xe9f5,0xea1d),(0x8252,0x8268),(0x77fe,0x780e),(0xda32,0xda36)]):self.serial_visits.add(ip)
  if ip==0xcd83:cpu.reg_write(UC_X86_REG_IP,0xe9f5);return
  if ip not in (0x4c3c,0x77fe,0xab0b,0x6b98,0x6b72,0x4e34):return super().on_code(cpu,address,size,_)
  if ip==0x77fe and self.actual_clock:return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);arg=self.word(sp+2);ax=dx=cleanup=0
  if ip==0x4c3c:
   assert arg==0 and self.rx_head<len(self.rx) and self.word(RXCOUNT)
   ax=self.rx[self.rx_head];self.rx_head+=1;self.put(RXCOUNT,len(self.rx)-self.rx_head);cleanup=2
  elif ip==0x77fe:
   value=self.clock_values[min(self.clock_reads,len(self.clock_values)-1)];self.clock_reads+=1;ax=value&65535;dx=value>>16
  elif ip==0xab0b:assert arg<=255;self.tx.append(arg);cleanup=2
  elif ip==0x6b98:self.pauses.append(arg);cleanup=2
  elif ip==0x6b72:self.delays.append(arg);cleanup=2
  else:
   self.polls+=1
   if self.arrivals:self.queued(self.arrivals.pop(0))
   else:ax=int(self.cancel_after!=0 and self.polls>=self.cancel_after)
  cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,dx)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def invoke(self,name,*args):
  self.actual_clock=name=='native_clock';self.actual_wait=False;self.reached=self.aborted=False;self.write(STACK-384,b'\xa5'*416)
  self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=2000000)
  if not self.aborted:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  flags=self.u.reg_read(UC_X86_REG_EFLAGS);assert not flags&0x400
  if self.actual_clock:assert flags&0x200
  for a,b,code in self.images:assert self.near_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)|(self.u.reg_read(UC_X86_REG_DX)<<16)
 def record(self):
  result=super().record();result.update(tx=self.tx,pauses=self.pauses,delays=self.delays,result=self.word(RESULT),rx_head=self.rx_head,
   remaining=self.word(RXCOUNT),clock_reads=self.clock_reads,serial_visits=sorted(self.serial_visits));return result


def suite(images):
 records=[];groups={};coverage=set();bank=DATA['bank']
 def done(m,g):records.append(m.record());groups[g]=groups.get(g,0)+1;coverage.update(m.serial_visits)
 for pattern in PATTERNS:
  for stream in STREAMS:
   for sensitive in (0,1):
    for far in (False,True):
     m=Machine(images,bytes([140 if far else 100,0])+timeout(0));m.put(CASE,sensitive);text=pattern+b'\0'+b'\0'*(81-len(pattern))
     if far:m.u.mem_write(0x5000*16+0x40,text)
     else:m.write(bank,text)
     m.queued(stream);m.invoke('wait_for');expected,consumed=match(decode(pattern),stream,sensitive)
     assert m.word(RESULT)==expected and m.rx_head==consumed and not m.clock_reads and m.position()==4
     done(m,'native_matcher_case_prefix_caret_near_far')
 for value in range(1,256):
  pattern=b'^^^' if value==94 else bytes([value]);m=Machine(images,b'\x64\0'+timeout(0));m.write(bank,pattern+b'\0\0');m.queued(bytes([value]));m.invoke('wait_for')
  assert m.word(RESULT)==1 and m.rx_head==1;done(m,'all_nonzero_match_bytes')
 for n in (0,1,2,79,80):
  m=Machine(images,b'\x64\0'+timeout(0));m.write(bank,b'X'*n+b'\0');m.queued(b'X'*max(n,1));m.invoke('wait_for');assert m.word(RESULT)==1 and m.rx_head==max(n,1);done(m,'pattern_lengths')
 # Prefix-only fallback deliberately misses the occurrence in AAAB.
 m=Machine(images,b'\x64\0'+timeout(0));m.write(bank,b'AAB\0');m.queued(b'AAAB');m.invoke('wait_for');assert not m.word(RESULT) and m.rx_head==4;done(m,'native_overlap_miss')
 m=Machine(images,b'\x64\0'+timeout(0));m.write(bank,b'Y\0');m.queued(b'X'*83);m.invoke('wait_for');assert m.rx_head==82 and m.word(RXCOUNT)==1 and m.polls==1;done(m,'eighty_two_byte_service_burst')
 # An idle cancellation poll makes source-owned next input available.
 m=Machine(images,b'\x64\0'+timeout(0));m.write(bank,b'OK\0');m.arrivals=[b'O',b'K'];m.invoke('wait_for');assert m.word(RESULT)==1 and m.polls==2;done(m,'partial_match_across_idle_service')
 timepairs=[(0,0),(0,17),(0,18),(100,99),(100,100),(100,117),(100,118),(100,65536),
  (DAY-10,DAY-1),(DAY-10,0),(DAY-10,7),(DAY-10,8),(DAY-10,9),(DAY-10,DAY-11),
  (DAY-18,DAY-1),(DAY-18,0),(0xfffffff0,0xfffffff0),(0xfffffff0,0),(0,0x80000000),
  (0x10000,0xffff),(0x10000,0x10000),(0x10000,0x20000),(0x20000,0x10000),
  (DAY+65536,DAY+65536),(DAY+65536,0),(DAY+65536,65535)]
 for count in (1,32767):
  for start,now in timepairs:
   m=Machine(images,b'\x64\0'+timeout(count));m.write(bank,b'X\0');m.clock_values=[start,now];m.invoke('wait_for')
   assert not m.word(RESULT) and m.clock_reads==2 and m.polls==int(not expired(count,start,now));done(m,'native_deadline_signed_daywrap')
 for value in (0,1,65535):
  m=Machine(images);m.put(RESULT,value);assert m.invoke('wait_status')&65535==value;done(m,'wait_status_raw_word')
 for option in (0,2,255,65535):
  m=Machine(images,b'' if option==65535 else bytes([option]));assert m.invoke('timeout_operand')&65535==30;done(m,'timeout_default_option')
 m=Machine(images,timeout(0));assert m.invoke('timeout_operand')&65535==0 and m.position()==2;done(m,'timeout_explicit_end')
 for value in (1,2,32767):
  m=Machine(images,timeout(value));assert m.invoke('timeout_operand')&65535==value and m.position()==4;done(m,'timeout_bounded_integer')
 for value in (0,32768,65535):
  for returns in (False,True):
   m=Machine(images,b'\1'+literal(value));m.string_error_returns=returns;m.invoke('timeout_operand')
   assert m.string_errors==[1] and m.aborted==(not returns);done(m,'timeout_error_return_or_stop')
 for echo in (0,1,65535):
  for text in [b'',b'AB^M^J^@C~D',b'^^^',b'END^']:
   m=Machine(images,b'\x64\0');m.write(bank,text+b'\0\0');m.put(ECHO,echo);m.put(DELAY,7);m.invoke('transmit');decoded=decode(text).split(b'\0')[0]
   tx=[0 if b==255 else b for b in decoded if b!=126];ordinary=[b for b in decoded if b not in (126,255)]
   assert m.tx==tx and m.emitted==(ordinary if echo else []) and m.pauses==[9]*decoded.count(126) and m.delays==[7]*len(ordinary);done(m,'transmit_caret_pause_nul_echo_delay')
 m=Machine(images,b'\x64\0');m.write(bank,b'^@\0');m.write(PAUSE,b'\xff');m.invoke('transmit');assert m.pauses==[9] and not m.tx and not m.delays;done(m,'pause_character_precedes_nul_escape')
 for value in range(1,256):
  text=b'^^^' if value==94 else bytes([value]);m=Machine(images,b'\x64\0');m.write(bank,text+b'\0\0');m.write(PAUSE,b'\0');m.invoke('transmit')
  assert m.tx==[0 if value==255 else value] and m.delays==([] if value==255 else [0]);done(m,'transmit_all_nonzero_bytes')
 for value in range(256):
  m=Machine(images);assert m.invoke('upper_byte',value)&65535==(value-32 if 97<=value<=122 else value);done(m,'actual_ctype_scalar_upper')
 for value in (0,1,0x12345678,DAY-1,0xffffffff):
  m=Machine(images);m.u.mem_write(0x46c,struct.pack('<I',value));assert m.invoke('native_clock')==value;done(m,'native_bios_clock_sample')
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nSERIAL >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_serial_commands.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[]
 for unit in manifest['units']:
  code=(OUT/unit['name']).read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
 assert [sha((OUT/f'serial-commands{i}.bin').read_bytes()) for i in range(1,8)]==EXPECTED
 serial_units=[unit for unit in manifest['units'] if unit['name'].startswith('serial-commands')]
 serial_bytes=sum(unit['end_exclusive']-unit['start'] for unit in serial_units)
 assert len(serial_units)==manifest['native_serial_units']==7 and serial_bytes==manifest['native_serial_bytes']==523
 records,groups,coverage=suite(images);optional=None
 expected={int(a,16) for a in re.findall(r'^serial_loc_([0-9a-f]+):',(ROOT/'src/aspect/serial_commands.asm').read_text(),re.M)}
 assert coverage==expected,(expected-coverage,coverage-expected)
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  assert [i for i,f in enumerate(original[0x25950+0x7caf:0x25950+0x7caf+256]) if f&2]==list(range(97,123))
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_serial_bytes=serial_bytes,exact_serial_ranges=len(serial_units),paired_cpu_scenarios=len(records),all_component_ranges=len(images))
 summary=dos_test()
 report=dict(passed=True,native_serial_bytes=serial_bytes,native_serial_ranges=len(serial_units),all_component_ranges=len(images),cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'SERIAL.EXE').read_bytes()),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256={p:sha((ROOT/'standalone'/p).read_bytes()) for p in ['check_aspect_console.py','check_aspect_string_commands.py','check_aspect_strings.py','check_aspect_operands.py','check_aspect_flow.py']},
  original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Native TRANSMIT/WAITFOR/format/timeout/scalar upper/status/BIOS clock with actual operand/string/caret code; serialreceive/send/delay/cancel/clock sampling callbacks modeled. No real UART/flowcontrol acceptance or complete VM claim; native matcher/time/bounds quirks preserved.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
