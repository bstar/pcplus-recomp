#!/usr/bin/env python3
"""Native string commands with actual text, operand, near/far copy services.

Only file/builtin/error/float-availability dependencies are modeled. This tests
command behavior rather than substituting text helpers. Native truncation and
returning-error policies remain distinct; no arbitrary-bytecode safety claim.
Optional original ranges are read only when --original is explicitly provided.
"""
import argparse,json,os,struct,subprocess
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_BP,
 UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_strings import Machine as StringMachine,CS,DS,STACK,STOP,DATA as STRING_DATA,BUILTIN
from build_aspect_string_commands import ROOT,OUT,SHA,ENTRIES,sha

COMPARE,INTEGER=0xd124,0xd482
EXPECTED=['eb347b24df15c26f78a4133db02c91a3ae54da5ca368a8fe91cec59284683595',
 'eb3a4f3dc8a045fffc2010660a8b139932acc3a5d56a257635cdea142996d008']


def literal(value):return b'\xab'+(value&65535).to_bytes(2,'little')
def pair(option=0,count=80,dest=b'\x64\0',source=b'\x64\1'):
 return dest+source+bytes([option])+(literal(count) if option==1 else b'')
def cmp(a,b):return 65535 if a<b else int(a>b)


class Machine(StringMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.put(COMPARE,0);self.put(INTEGER,0);self.command_visits=set()
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if 0xeeff<=ip<0xef1d or 0xef42<=ip<0xf0b5:self.command_visits.add(ip)
  if ip==0xdd26:self.aborted=True;cpu.emu_stop();return
  if ip!=0x4efb:return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);code=self.word(sp+2);assert code in (1,3)
  self.string_errors.append(code)
  if not self.string_error_returns:self.aborted=True;cpu.emu_stop();return
  cpu.reg_write(UC_X86_REG_AX,0);cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+4)
 def invoke(self,name):
  self.reached=self.aborted=False;self.write(STACK-128,b'\xa5'*144);self.put(STACK,STOP)
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=100000)
  if not self.aborted:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert self.near_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)
 def near_code(self,a,b):return bytes(self.u.mem_read(CS*16+a,b-a))
 def record(self):
  result=super().record();result.update(comparison=self.word(COMPARE),integer=self.word(INTEGER),bank=self.near(STRING_DATA['bank'],243).hex(),command_visits=sorted(self.command_visits));return result


def suite(images):
 records=[];coverage=set();groups={};bank=STRING_DATA['bank']
 def done(m,group):records.append(m.record());coverage.update(m.command_visits);groups[group]=groups.get(group,0)+1
 for n in range(81):
  for name in ('compare_bytes','compare'):
   a=bytes([65])*80+b'\0';b=bytearray(a)
   if n:b[n-1]=66
   m=Machine(images,pair(1,n));m.write(bank,a+bytes(b));m.invoke(name)
   assert m.word(COMPARE)==cmp(a[:n],b[:n]);done(m,'bounded_compare')
 for a in (0,1,65,97,127,128,255):
  for b in (0,1,65,97,127,128,255):
   m=Machine(images,pair());m.write(bank,bytes([a,0])+b'Q'*79+bytes([b,0])+b'R'*79);m.invoke('compare')
   assert m.word(COMPARE)==cmp(bytes([a]),bytes([b]));done(m,'unsigned_compare')
 for dest_length in (0,1,2,39,79,80):
  for source_length in (0,1,2,39,79,80):
   for option in (0,1):
    for requested in ((0,1,2,39,79,80) if option else (source_length,)):
     for returns in (False,True):
      wire=pair(option,requested,source=b'\x6e\0');m=Machine(images,wire)
      before=b'D'*dest_length+b'\0'+b'Q'*(80-dest_length);src=b'S'*source_length+b'\0'+b'R'*(80-source_length)
      m.write(bank,before);m.write(BUILTIN,src);m.string_error_returns=returns;m.invoke('concat')
      wanted=requested if option else source_length;bad=dest_length+wanted>80
      assert m.string_errors==([3] if bad else []) and m.aborted==(bad and not returns)
      expected=bytearray(before)
      if not m.aborted:
       used=min(source_length,min(wanted,80-dest_length));expected[dest_length:dest_length+used]=b'S'*used;expected[dest_length+used]=0
      assert m.near(bank,81)==expected;done(m,'concat_truncation_policy')
 for n in range(81):
  m=Machine(images,b'\x64\0\x8d\0');m.write(bank,b'L'*n+b'\0'+b'Q'*(80-n));m.invoke('length')
  assert m.word(INTEGER)==n;done(m,'length_store')
 for value in range(1,256):
  for name in ('lower','upper'):
   m=Machine(images,b'\x64\0');m.write(bank,bytes([value,0]));m.invoke(name)
   expected=value+32 if name=='lower' and 65<=value<=90 else value-32 if name=='upper' and 97<=value<=122 else value
   assert m.near(bank,2)==bytes([expected,0]);done(m,'ASCII_case_and_highbytes')
 for index in range(80):
  m=Machine(images,b'\x64\0'+literal(index)+b'\x8d\0');m.write(bank,bytes((i*73+19)&255 for i in range(81)));expected=m.near(bank+index,1)[0];m.invoke('get_char')
  assert m.word(INTEGER)==expected;done(m,'get_char')
  m=Machine(images,b'\x64\0'+literal(index)+literal(255-index));before=bytes((i*73+19)&255 for i in range(81));m.write(bank,before);m.invoke('set_char')
  expected=bytearray(before);expected[index]=255-index;assert m.near(bank,81)==expected;done(m,'set_char')
 for value in (0,1,65,128,255):
  for count in range(81):
   m=Machine(images,b'\x64\0'+literal(value)+b'\1'+literal(count));before=b'Q'*81;m.write(bank,before);m.invoke('fill')
   assert m.near(bank,81)==bytes([value])*count+b'Q'*(80-count)+b'\0';done(m,'fill_exact_bytes')
 for index in (0,1,7,39,79):
  for count in (0,1,2,39,79,80):
   for returns in (False,True):
    for alias in (False,True):
     source=b'\x64\0' if alias else b'\x64\1';wire=b'\x64\0'+source+literal(index)+literal(count)
     m=Machine(images,wire);before=bytes((i*37+1)&255 for i in range(243));m.write(bank,before);m.string_error_returns=returns;m.invoke('subcopy')
     bad=index+count>80;assert m.string_errors==([3] if bad else []) and m.aborted==(bad and not returns)
     expected=bytearray(before)
     if not m.aborted:
      n=min(count,80-index);start=0 if alias else 81;expected[index:index+n]=before[start:start+n];expected[80]=0
     assert m.near(bank,243)==expected;done(m,'subcopy_overlap_and_error')
   for alias in (False,True):
    source=b'\x64\0' if alias else b'\x64\1';wire=b'\x64\0'+source+literal(index)+literal(count)
    m=Machine(images,wire);before=bytes((i*37+1)&255 for i in range(243));m.write(bank,before);m.invoke('substr')
    expected=bytearray(before);start=(0 if alias else 81)+index;expected[:count]=before[start:start+count];expected[count]=0
    assert not m.string_errors and m.near(bank,243)==expected;done(m,'substr_overlap_and_unchecked_span')
 for name,tail in [('lower',b''),('upper',b''),('set_char',literal(1)+literal(88)),('fill',literal(90)+b'\1'+literal(3)),
                   ('concat',b'\x6e\0\0'),('subcopy',b'\x6e\0'+literal(1)+literal(2)),('substr',b'\x6e\0'+literal(1)+literal(2))]:
  m=Machine(images,b'\x8c\0'+tail);before=b'aBc\0'+b'Q'*77;m.u.mem_write(0x5000*16+0x40,before);m.write(BUILTIN,b'SRC\0'+b'R'*77);m.invoke(name)
  expected=bytearray(before)
  if name=='lower':expected[:3]=b'abc'
  elif name=='upper':expected[:3]=b'ABC'
  elif name=='set_char':expected[1]=88
  elif name=='fill':expected[:3]=b'ZZZ';expected[80]=0
  elif name=='concat':expected[3:7]=b'SRC\0'
  elif name=='subcopy':expected[1:3]=b'SR';expected[80]=0
  else:expected[:3]=b'RC\0'
  assert m.far(0)==expected and m.word(STRING_DATA['pending_near'])==0;done(m,'actual_far_writeback')
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
STRCMD >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_string_commands.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[]
 for unit in manifest['units']:
  code=(OUT/unit['name']).read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
 assert [sha((OUT/f'commands{i}.bin').read_bytes()) for i in (1,2)]==EXPECTED
 records,groups,coverage=suite(images);optional=None
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_command_bytes=401,paired_cpu_scenarios=len(records),all_component_ranges=len(images))
 summary=dos_test()
 report=dict(passed=True,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,binary_sha256=sha((OUT/'STRCMD.EXE').read_bytes()),
  check_sha256=sha(Path(__file__).read_bytes()),inherited_checker_sha256=sha((ROOT/'standalone/check_aspect_strings.py').read_bytes()),original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='11actual string commands and real text CRT/string/operand/frame/copy services. File,builtin,error,unavailable-float callback policies explicit. Returning error3 truncation, nonreturning error3 preservation, byte/high-character behavior, overlap and real far writeback tested. SUBSTR retains unchecked source index+count span. No full VM or arbitrary-input safety claim.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
