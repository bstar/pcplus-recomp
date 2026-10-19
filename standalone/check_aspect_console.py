#!/usr/bin/env python3
"""Actual native console handlers with explicit byte/cancel/wait platform callbacks.

CPU delay tests advance a controlled BIOS lowword clock; DOS tests also execute
native BIOS waits. Ordinary checks use maintained source; --original is optional.
"""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_string_commands import Machine as BaseMachine
from check_aspect_strings import CS,DS,STACK,STOP,DATA,BUILTIN
from build_aspect_console import ROOT,OUT,SHA,ENTRIES,sha

EXPECTED=['c072e61f2b3198634ab97e89956f8eff7118d73376a3a1483c6a28348491cc92', 'dd382b76b3032825a6dbf2aec921693077821fd914878f0eb5ddeab698d41388', 'a2982584b22e1a987689aa382256de2cba6b7b65edff43e52514c69354c4c49e', '008b9051520b45049c2a7c95767686eb48fa3951da532a8abc18de9ead0f9b43', 'ee3b685777972efbddd1963529ec5be1dc4891f9b53ce3e1362facba344f270d', '01ce9602651b49f69bddd78c501dcef8d30551c6c8cad7fbe608d3a9ce3e1694', '6da85740c30fe8a57a9644f2d2e848615111bedb9ce9809b333cadbf16cfd413']
MODE,COMPARE=0xe38a,0xd124
CASES=[b'',b'HELLO',b'^@',b'^^',b'^^^',b'^^^^',b'A^GB',b'^[31mRED^[0m',b'^A^B^C^D',b'^z^a^?',b'END^']
def literal(value):return b'\xab'+struct.pack('<H',value&65535)
def decode(text):
 text+=b'\0\0';out=bytearray();i=0
 while text[i]:
  b=text[i];i+=1
  if b==94:
   b=text[i];i+=1
   if b==64:b=255
   elif b==94 and text[i]==94:b=94;i+=1
   else:b&=31
  out.append(b)
 return bytes(out)


class Machine(BaseMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.put(MODE,1);self.put(COMPARE,0);self.emitted=[];self.polls=self.waits=0;self.cancel_after=0
  self.console_visits=set();self.ticks=0xfffe;self.tick_stride=1;self.tick_probes=self.tick_changes=0
  self.u.mem_write(0x46c,struct.pack('<H',self.ticks))
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if any(a<=ip<b for a,b in [(0x4eb5,0x4ebc),(0x5029,0x5058),(0x507b,0x50aa),(0x4934,0x498b),(0x3abd,0x3af8),(0xdd9c,0xdda7),(0x6b98,0x6bbe)]):self.console_visits.add(ip)
  if ip==0x6ba9:
   self.tick_probes+=1
   if self.tick_probes%3==0:
    self.tick_changes+=1;self.ticks=(self.ticks+self.tick_stride)&65535;self.u.mem_write(0x46c,struct.pack('<H',self.ticks))
  # Resolve the original resident overlay thunks into actual maintained bodies.
  if ip in (0xce1f,0xcdd7):cpu.reg_write(UC_X86_REG_IP,0xdf04 if ip==0xce1f else 0xdd9c);return
  if ip not in (0x610,0x4e34,0x6bb6):return super().on_code(cpu,address,size,_)
  # The actual native second-delay entry remains selectable directly.
  if ip==0x6bb6 and self.actual_wait:return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);ax=0
  if ip==0x610:
   value=self.word(sp+2);assert value<=255;self.emitted.append(value)
  elif ip==0x4e34:self.polls+=1;ax=int(self.cancel_after!=0 and self.polls>=self.cancel_after)
  else:self.waits+=1
  cpu.reg_write(UC_X86_REG_AX,ax);cpu.reg_write(UC_X86_REG_DX,0xbeef)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2)
 def invoke(self,name,*args):
  self.actual_wait=name.startswith('native_wait');self.reached=self.aborted=False;self.write(STACK-256,b'\xa5'*288)
  self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=2000000)
  if not self.aborted:
   cleanup=2 if name=='native_wait_ticks' else 0
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+cleanup
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  flags=self.u.reg_read(UC_X86_REG_EFLAGS);assert not flags&0x400
  if self.actual_wait:assert flags&0x200
  for a,b,code in self.images:assert self.near_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)
 def record(self):
  result=super().record();result.update(emitted=self.emitted,polls=self.polls,waits=self.waits,
   compare=self.word(COMPARE),exit_state=self.word(DATA['exit_state']),tick_changes=self.tick_changes,ticks=self.ticks,console_visits=sorted(self.console_visits));return result


def suite(images):
 records=[];groups={};coverage=set();bank=DATA['bank']
 def done(m,g):records.append(m.record());groups[g]=groups.get(g,0)+1;coverage.update(m.console_visits)
 def message(text,mode=1,far=False):
  m=Machine(images,bytes([140 if far else 100,0]));m.put(MODE,mode);backing=text+b'\0'+bytes(82-len(text))
  if far:m.u.mem_write(0x5000*16+0x40,backing)
  else:m.write(bank,backing)
  m.invoke('message');expected=decode(text).split(b'\0')[0]+(b'\r\n' if mode else b'')
  assert bytes(m.emitted)==expected and m.position()==2 and not m.aborted
  return m
 for text in CASES:
  for mode in (0,1,65535):
   for far in (False,True):done(message(text,mode,far),'message_caret_and_line_mode_near_far')
 for value in range(1,256):done(message(bytes([value])+ (b'A' if value==94 else b'')),'message_all_nonzero_byte_values')
 for n in range(81):done(message(b'X'*n),'message_all_valid_lengths')
 for value in (0,1,999,65535):
  m=Machine(images);m.put(DATA['exit_state'],value);m.invoke('exit');assert m.word(DATA['exit_state'])==1 and not m.emitted and not m.polls and not m.waits;done(m,'exit_native_state')
 for count in (0,1,2,17,255):
  for stop in (0,1,2,17,256):
   m=Machine(images,literal(count));m.cancel_after=stop;m.invoke('pause');cancelled=0<stop<=count
   assert m.word(COMPARE)==cancelled and m.polls==(stop if cancelled else count) and m.waits==(stop-1 if cancelled else count)
   assert m.position()==3 and not m.aborted;done(m,'pause_completion_and_cancel_position')
 # Stop early to examine signed result for otherwise unchecked negative counts.
 for count in (32767,32768,32769,65535):
  for checking in (False,True):
   for returns in (False,True):
    m=Machine(images,literal(count));m.put(DATA['check_range'],checking);m.string_error_returns=returns;m.cancel_after=1;m.invoke('pause')
    bad=checking and count>32767;assert m.string_errors==([1] if bad else []) and m.aborted==(bad and not returns)
    if not m.aborted:assert m.polls==1 and not m.waits and m.word(COMPARE)==int(((count-1)&65535)<32768)
    else:assert not m.polls and not m.waits
    done(m,'pause_native_range_error_return_or_stop')
 for count in (0,1,18,255,65535):
  for stride in (1,13):
   m=Machine(images);m.tick_stride=stride;m.invoke('native_wait_ticks',count)
   changes=(count+1)&65535 or 1;assert m.tick_changes==changes and m.ticks==(0xfffe+changes*stride)&65535
   done(m,'native_delay_tick_transition_count_and_wrap')
 m=Machine(images);m.invoke('native_wait_second');assert m.tick_changes==19;done(m,'native_one_second_nineteen_transitions')
 # Actual decoder destination and source guard; native has no capacity argument.
 m=Machine(images);m.write(BUILTIN,b'A^^^B^@C^Z\0\0');m.write(0x6000,b'Q'*81);m.invoke('decode',BUILTIN,0x6000);expected=decode(b'A^^^B^@C^Z')+b'\0'
 assert m.near(0x6000,len(expected)+1)==expected+b'Q';done(m,'actual_decoder_guard')
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nCONSOLE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_console.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[]
 for unit in manifest['units']:
  code=(OUT/unit['name']).read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
 assert [sha((OUT/f'console{i}.bin').read_bytes()) for i in range(1,8)]==EXPECTED
 records,groups,coverage=suite(images);optional=None
 expected={int(a,16) for a in re.findall(r'^console_loc_([0-9a-f]+):',(ROOT/'src/aspect/console_commands.asm').read_text(),re.M)}
 assert coverage==expected,(expected-coverage,coverage-expected)
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_console_bytes=296,paired_cpu_scenarios=len(records),all_component_ranges=len(images))
 summary=dos_test()
 report=dict(passed=True,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'CONSOLE.EXE').read_bytes()),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256={p:sha((ROOT/'standalone'/p).read_bytes()) for p in ['check_aspect_string_commands.py','check_aspect_strings.py','check_aspect_operands.py','check_aspect_flow.py']},
  original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Native console commands/caret decoder/print loops/bounded pause operand/BIOS delay with actual string/numeric/lvalue/frame/copy code. Byte renderer, cancel, PAUSE wait calls controlled. CPU clock controlled; DOS executes native BIOS delays. Native unchecked caret/buffer/range behavior retained; no complete VM or arbitrary-input safety.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
