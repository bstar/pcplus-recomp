#!/usr/bin/env python3
"""Native receive commands and explicit device/clock component boundaries."""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_serial_commands import Machine as BaseMachine
from check_aspect_strings import CS,DS,STACK,STOP,DATA,BUILTIN
from build_aspect_receive_commands import ROOT,OUT,SHA,ENTRIES,UNITS,sha
EXPECTED=['b1bca0d74bd8400e257f8f95382924d09cc686d05e0da1d6a8ccc713fc9d527d', '3a7b1a966aeacc8512c37da746f79b4315ff9969247dd5b8e8ed753bf70af7ef', '3089522a649a35998ee72290fdfe9443825ed70528813ef57ae6ce206a0f6edd', 'bcd3e278a5abd66a7affffab68faa63376b6ef762ee1a081e06d94b615d4daf5', '5291a203c0c84b71b85b0a50febcd985e2070c672d8ba557d95e652b87140d74', 'c677c642aab995664be684bbcd61ded5f3be8491c1d7a89e8167fb50b53680d0', 'cac3b64b4124d89b51def2913c187db7517d1ae30e2903f47f8ff2366779e7e5', '0029bd0ba5c96b2bc0758aee72a1229e5eeee0182e164a8c6b1571f285d17e41', '4e5f23d1d891cee5500f23bb57d13c3f5e89a82580b2492986a809fc87339519']
DISPLAY,SUPPRESS,COMPARE,RXCOUNT,SAMPLE=0xe37e,0xe382,0xd124,0x8e20,0x8f02

def literal(value):return b'\xab'+struct.pack('<H',value&65535)
def rget_wire(limit=80,seconds=30,destination=b'\x64\0'):
 return destination+b'\1'+literal(limit)+b'\1'+literal(seconds)
def quiet_wire(quiet,seconds):return b'\1'+literal(quiet)+b'\1'+(literal(seconds) if seconds else b'\x1a')


class Machine(BaseMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.put(DISPLAY,0);self.put(SUPPRESS,0);self.put(COMPARE,0);self.write(SAMPLE,bytes(8))
  self.device_calls=[];self.raw_calls=0;self.seconds_values=[];self.seconds_head=self.seconds_tail=0
  self.wait_arrivals=[];self.receive_visits=set();self.cancel_after=0
  self.tick_reads=self.delayed_tick_changes=0;self.delayed_arrival=None;self.delay_tick=65534
  self.dos_time=(23,59,58,99);self.builtin_returns=[]
  self.u.mem_write(0x46c,struct.pack('<H',self.delay_tick))
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if any(a<=ip<b for _,a,b,_ in UNITS):self.receive_visits.add(ip)
  aliases={0xce13:0xde4d,0xce2b:0xdf0b,0xcd5f:0xe0e4,0xcde3:0xde11,0xcdd7:0xdd9c,0xcd47:0xe0a4}
  if ip in aliases:cpu.reg_write(UC_X86_REG_IP,aliases[ip]);return
  if ip==0xf900:
   target=self.builtin_returns.pop();sp=cpu.reg_read(UC_X86_REG_SP);cpu.reg_write(UC_X86_REG_SP,sp+2);cpu.reg_write(UC_X86_REG_IP,target);return
  if ip==0xd988:
   sp=cpu.reg_read(UC_X86_REG_SP);index=self.word(sp+2)
   if index in (20,22):
    self.builtin_returns.append(self.word(sp));self.put(sp,0xf900);cpu.reg_write(UC_X86_REG_IP,0xda08 if index==20 else 0xda10);return
  if ip==0x5cbc:
   self.tick_reads+=1
   if self.tick_reads%3==0:
    self.delayed_tick_changes+=1;self.delay_tick=(self.delay_tick+1)&65535;self.u.mem_write(0x46c,struct.pack('<H',self.delay_tick))
    if self.delayed_arrival==self.delayed_tick_changes:self.queued(b'Q')
  if ip not in (0x4c74,0xaa65,0x3323,0x6bb6):return super().on_code(cpu,address,size,_)
  if ip==0x3323 and self.actual_seconds:return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);ax=cleanup=0
  if ip in (0x4c74,0xaa65):
   if ip==0x4c74:self.device_calls.append((self.word(sp+2),self.word(sp+4)));cleanup=4
   self.raw_calls+=1
   if self.rx_head>=len(self.rx):ax=65535
   else:ax=self.rx[self.rx_head];self.rx_head+=1;self.put(RXCOUNT,len(self.rx)-self.rx_head)
  elif ip==0x3323:
   i=self.seconds_head;self.seconds_head+=1
   if self.seconds_values:ax=self.seconds_values[min(i,len(self.seconds_values)-1)]
   elif self.word(RXCOUNT):ax=0
   else:ax=(self.seconds_tail//2)%60;self.seconds_tail+=1
  else:
   self.waits+=1
   if self.wait_arrivals:self.queued(self.wait_arrivals.pop(0))
  cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,0xbeef)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def interrupt(self,cpu,number,_):
  assert number==0x21 and cpu.reg_read(UC_X86_REG_AX)>>8==0x2c
  h,m,s,cs=self.dos_time;cpu.reg_write(UC_X86_REG_CX,h<<8|m);cpu.reg_write(UC_X86_REG_DX,s<<8|cs)
 def invoke(self,name,*args):
  self.actual_seconds=name in ('native_seconds','native_time');self.actual_clock=self.actual_wait=False
  self.reached=self.aborted=False;self.write(STACK-384,b'\xa5'*416);self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=2000000)
  if not self.aborted:
   cleanup=2 if name in ('read_integer','read_control','native_time') else 0
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+cleanup and not self.builtin_returns
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  flags=self.u.reg_read(UC_X86_REG_EFLAGS);assert not flags&0x400
  if self.tick_reads:assert flags&0x200
  for a,b,code in self.images:assert self.near_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)
 def record(self):
  result=super().record();result.update(receive_visits=sorted(self.receive_visits),device_calls=self.device_calls,raw_calls=self.raw_calls,
   seconds_reads=self.seconds_head,delay_changes=self.delayed_tick_changes,sample=self.near(SAMPLE,8).hex());return result


def suite(images):
 records=[];groups={};coverage=set();bank=DATA['bank']
 def done(m,g):records.append(m.record());groups[g]=groups.get(g,0)+1;coverage.update(m.receive_visits)
 for name in ('comgetc','comgetcd'):
  for display in (0,1,65535):
   for suppress in (0,1,2,65535):
    for value in (0,13,127,128,255,65535):
     m=Machine(images,b'\x8d\0');m.put(DISPLAY,display);m.put(SUPPRESS,suppress)
     if value!=65535:m.queued(bytes([value]))
     m.invoke(name);assert m.word(0xd482)==value and m.device_calls==[(int(bool(display) and not suppress),int(name=='comgetcd'))] and m.position()==2
     done(m,'comget_flags_values_and_store')
 for index in range(256):
  m=Machine(images,bytes([141,index]));m.queued(bytes([255-index]));m.invoke('comgetc');assert m.word(0xd482+index*2)==255-index;done(m,'integer_destination_indices')
 for limit in range(1,81):
  for mode in (0,1,2):
   m=Machine(images,rget_wire(limit));m.write(bank,b'Z'*82);length=limit+int(mode==0);stream=bytearray(b'A'*length)
   if mode:stream[limit//2 if mode==1 else 0]=13
   m.queued(stream);m.invoke('rget');n=limit if not mode else limit//2 if mode==1 else 0
   assert m.near(bank,n+2)==b'A'*n+b'\0Z' and m.rx_head==n+int(bool(mode)) and m.word(COMPARE)==0
   assert m.position()==10 and m.word(DATA['pending_near'])==0;done(m,'rget_all_lengths_full_and_cr')
 for far in (False,True):
  m=Machine(images,rget_wire(80,destination=bytes([140 if far else 100,0])));before=b'Z'*81
  if far:m.u.mem_write(0x5000*16+0x40,before)
  else:m.write(bank,before)
  m.queued(b'A\0B\r');m.invoke('rget');assert (m.far(0) if far else m.near(bank,81))==b'A\0B\0'+before[4:];done(m,'rget_embedded_nul_and_far_writeback')
 m=Machine(images,rget_wire(0));m.queued(b'A\r');m.invoke('rget');assert m.near(bank,2)==b'A\0' and m.rx_head==2 and not m.word(COMPARE);done(m,'native_zero_requested_length_quirk')
 m=Machine(images,rget_wire(80,0));m.queued(b'A');m.invoke('rget');assert m.word(COMPARE)==1 and not m.rx_head and not m.polls and m.seconds_head==1;done(m,'zero_timeout_skips_receive')
 for seconds,seq in [(1,[59,0,0]),(2,[0,10,10,20,20]),(2,[0,0,0,1,1,2,2])]:
  m=Machine(images,rget_wire(80,seconds));m.seconds_values=seq;m.invoke('rget');assert m.word(COMPARE)==1 and m.seconds_head==len(seq);done(m,'observed_seconds_changes_and_wrap')
 m=Machine(images,rget_wire());m.cancel_after=1;m.queued(b'A');m.invoke('rget');assert not m.word(COMPARE) and not m.rx_head and m.near(bank,1)==b'\0';done(m,'cancel_is_native_rget_status_zero')
 m=Machine(images,b'\x64\0\0');m.queued(b'OK\r');m.invoke('rget');assert m.near(bank,3)==b'OK\0' and m.position()==3;done(m,'default_length_timeout')
 m=Machine(images,rget_wire()[:7]+b'\x6f\x16');m.seconds_values=[0,1,1];m.invoke('rget');assert m.word(COMPARE)==1 and m.seconds_head==3 and m.position()==9;done(m,'actual_forever_builtin_is_one')
 for quiet in (0,1,2,15,31):
  for total in (0,1,2,30,31):
   m=Machine(images,quiet_wire(quiet,total));m.invoke('wait_quiet');incomplete=bool(quiet and total and total<quiet)
   assert m.word(COMPARE)==incomplete and m.waits==(min(quiet,total) if total else quiet);done(m,'quiet_completion_total_timeout_unlimited')
 m=Machine(images,b'\0');m.invoke('wait_quiet');assert not m.word(COMPARE) and m.waits==15 and m.position()==1;done(m,'quiet_default_fifteen_thirty')
 m=Machine(images,quiet_wire(2,8));m.wait_arrivals=[b'A',b'BC'];m.invoke('wait_quiet');assert not m.word(COMPARE) and m.waits==4 and m.rx_head==2;done(m,'quiet_drains_and_resets_after_arrivals')
 m=Machine(images,quiet_wire(2,8));m.cancel_after=1;m.invoke('wait_quiet');assert m.word(COMPARE)==1 and not m.waits;done(m,'quiet_cancel')
 for value in (0,1,4096,65535):
  m=Machine(images);m.put(RXCOUNT,value);assert m.invoke('available_status')==value;assert m.invoke('forever')==1;done(m,'native_comdata_forever_words')
 for value in (0,13,255):
  m=Machine(images);m.queued(bytes([value]));assert m.invoke('native_delayed_read')==value and m.raw_calls==1 and not m.tick_reads;done(m,'native_delayed_immediate_available')
 for arrival in (None,1,17,36):
  m=Machine(images);m.delayed_arrival=arrival;value=m.invoke('native_delayed_read')
  assert value==(65535 if arrival in (None,36) else ord('Q')) and m.delayed_tick_changes==(36 if arrival is None else arrival)
  if arrival==36:assert m.word(RXCOUNT)==1 and not m.raw_calls
  done(m,'native_delayed_thirtysix_transitions_or_arrival')
 for sample in [(0,0,0,0),(23,59,59,99),(12,34,56,78)]:
  m=Machine(images);m.dos_time=sample;m.write(0x6000,b'Q'*10);m.invoke('native_time',0x6000);h,mi,se,cs=sample
  assert m.near(0x6000,10)==struct.pack('<HHHH',cs,h,mi,se)+b'QQ';assert m.invoke('native_seconds')==se and m.near(SAMPLE,8)==struct.pack('<HHHH',cs,h,mi,se);done(m,'native_dos_time_struct_and_seconds')
 # Native range faults happen after selecting writable scratch, before flush.
 for limit in (81,65535):
  for returns in (False,True):
   m=Machine(images,rget_wire(limit,destination=b'\x8c\0'));m.string_error_returns=returns;m.cancel_after=1;before=m.far(0);m.invoke('rget')
   assert m.string_errors==[1] and m.aborted==(not returns)
   if not returns:assert m.far(0)==before and m.word(DATA['pending_near'])!=0
   done(m,'range_fault_before_far_writeback_or_return')
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nRECEIVE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_receive_commands.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[]
 for unit in manifest['units']:
  code=(OUT/unit['name']).read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
 assert [sha((OUT/f'receive-commands{i}.bin').read_bytes()) for i in range(1,10)]==EXPECTED
 receive_units=[unit for unit in manifest['units'] if unit['name'].startswith('receive-commands')]
 receive_bytes=sum(unit['end_exclusive']-unit['start'] for unit in receive_units)
 assert len(receive_units)==manifest['native_receive_units']==9 and receive_bytes==manifest['native_receive_bytes']==435
 records,groups,coverage=suite(images);optional=None
 expected={int(a,16) for a in re.findall(r'^receive_loc_([0-9a-f]+):',(ROOT/'src/aspect/receive_commands.asm').read_text(),re.M)}
 assert coverage==expected,(expected-coverage,coverage-expected)
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_receive_bytes=receive_bytes,exact_receive_ranges=len(receive_units),paired_cpu_scenarios=len(records),all_component_ranges=len(images))
 summary=dos_test()
 report=dict(passed=True,native_receive_bytes=receive_bytes,native_receive_ranges=len(receive_units),all_component_ranges=len(images),cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'RECEIVE.EXE').read_bytes()),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256={p:sha((ROOT/'standalone'/p).read_bytes()) for p in ['check_aspect_serial_commands.py','check_aspect_console.py','check_aspect_string_commands.py','check_aspect_strings.py','check_aspect_operands.py','check_aspect_flow.py']},
  original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Native COMGETC/Cd/RGET/WAITQUIET/read selector/delayed read/DOS time/COMDATA20/FOREVER22 with actual operands/string/far writeback.4C74/device/seconds/wait/cancel callbacks controlled; directCPUclockandDOSINT21samples modeled, directDOSdelay/time actual. Native zero-length/seconds/cancel/drain quirks preserved; no fullUART/translation/patternmonitor/renderer or application acceptance claim.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
