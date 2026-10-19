#!/usr/bin/env python3
"""Check actual conversion commands/scanner/CRT with native operand/string code.

Only file, builtin, invalid/error and unavailable float services are controlled
component callbacks. --original performs a separate private exact/paired check.
"""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_BP,
 UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_string_commands import Machine as BaseMachine
from check_aspect_strings import CS,DS,STACK,STOP,DATA,BUILTIN
from build_aspect_conversions import ROOT,OUT,SHA,ENTRIES,sha

EXPECTED=['83d7e5fe84f55bc2f5ccc6181f01ded29f69d5823c4360f42a94d82565762f29',
 '5b50ec3955b5c0ad85fbb06e915a1be03d6dbc20509f6f47e7d92439c53215e2']
CASES=[b'',b'x',b'0',b'-0',b'+123',b'prefix=-123suffix',b'.25',b'-.25',b'--123',
 b'-x.42',b'1.234',b'+x-9',b'32767',b'32768',b'-32768',b'-32769',b'65535',b'65536',
 b'2147483647',b'2147483648',b'-2147483648',b'-2147483649',b'4294967295',b'4294967296',
 b'999999999999999999999999999999999999',b'abc- def.ghi9',b'abc-',b'abc.',b'  +27',b'\t-42',b'\n99']

def literal(value):return b'\xab'+struct.pack('<H',value&65535)
def wide(value):return b'\xac'+struct.pack('<I',value&0xffffffff)
def signed(value,bits):return value-(1<<bits) if value>>(bits-1) else value
def scan(text,flag):
 for i,b in enumerate(text):
  if 48<=b<=57 or (b==45 or flag and b==46) and i+1<len(text) and 48<=text[i+1]<=57:return i
 return len(text)
def parse(text):
 text=text.lstrip(b' \t');negative=text.startswith(b'-')
 if text[:1] in (b'+',b'-'):text=text[1:]
 value=0
 for b in text:
  if not 48<=b<=57:break
  value=(value*10+b-48)&0xffffffff
 return (-value if negative else value)&0xffffffff


class Machine(BaseMachine):
 def __init__(self,images,data=b''):
  super().__init__(images,data)
  self.write(0x776c,b'-.0123456789\0');self.write(0x7caf,bytes(4 if 48<=i<=57 else 0 for i in range(256)))
  self.conversion_visits=set()
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if 0xea4b<=ip<0xeae1 or 0xeaf4<=ip<0xeb38:self.conversion_visits.add(ip)
  return super().on_code(cpu,address,size,_)
 def invoke(self,name,*args):
  self.reached=self.aborted=False;self.write(STACK-128,b'\xa5'*160)
  self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=100000)
  if not self.aborted:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+2*len(args)
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert self.near_code(a,b)==code
  return self.u.reg_read(UC_X86_REG_AX)
 def record(self):
  result=super().record();result.update(long_result=self.long(0xd582),ax=self.u.reg_read(UC_X86_REG_AX),
   dx=self.u.reg_read(UC_X86_REG_DX),conversion_visits=sorted(self.conversion_visits));return result


def suite(images):
 records=[];groups={};coverage=set();bank=DATA['bank']
 def done(m,group):records.append(m.record());groups[group]=groups.get(group,0)+1;coverage.update(m.conversion_visits)
 for text in CASES:
  for flag in (0,1,65535):
   m=Machine(images);m.write(BUILTIN,text+b'\0');assert m.invoke('scan_numeric',flag,BUILTIN)==BUILTIN+scan(text,flag);done(m,'scanner_candidates_sign_dot_and_empty')
  expected=parse(text[scan(text,False):])
  for name in ('atoi','atol'):
   m=Machine(images,b'\x64\0'+bytes([141 if name=='atoi' else 142,0]));m.write(bank,text+b'\0');m.invoke(name)
   assert (m.word(0xd482) if name=='atoi' else m.long(0xd582))==(expected&65535 if name=='atoi' else expected)
   assert m.position()==4 and not m.aborted;done(m,'atoi_atol_prefix_and_overflow')
 for b in range(256):
  text=bytes([b])+b'-x.9';text=text.split(b'\0')[0]
  for flag in (0,1):
   m=Machine(images);m.write(BUILTIN,text+b'\0');assert m.invoke('scan_numeric',flag,BUILTIN)==BUILTIN+scan(text,flag);done(m,'scanner_all_byte_values')
 for name in ('itoa','ltoa'):
  bits=16 if name=='itoa' else 32
  values={0,1,(1<<(bits-1))-1,1<<(bits-1),(1<<bits)-1}
  values.update((i*0x01010101)&((1<<bits)-1) for i in range(256))
  for value in sorted(values):
   expected=str(signed(value,bits)).encode()+b'\0'
   for far in (False,True):
    wire=(literal(value) if bits==16 else wide(value))+bytes([140 if far else 100,0])
    m=Machine(images,wire);before=b'Z'*81
    if far:m.u.mem_write(0x5000*16+0x40,before)
    else:m.write(bank,before)
    m.invoke(name);actual=m.far(0) if far else m.near(bank,81)
    assert actual==expected+before[len(expected):] and m.word(DATA['pending_near'])==0
    assert m.position()==len(wire) and not m.aborted;done(m,'decimal_format_and_actual_far_flush')
 # The scanner depends on the supplied table bit, not an invented Unicode class.
 for b in (45,46):
  m=Machine(images);m.write(BUILTIN,bytes([b])+b'x\0');m.write(0x7caf+b,b'\4')
  assert m.invoke('scan_numeric',0,BUILTIN)==BUILTIN;done(m,'mutable_native_ctype_bit')
 # Normal nonreturning invalid-operand service versus deliberately returning model.
 for name in ('atoi','atol'):
  for returns in (False,True):
   m=Machine(images,b'\x64\0\x63');m.write(bank,b'-42\0');m.invalid_returns=returns;m.invoke(name)
   assert m.invalids==1 and m.aborted==(not returns)
   if returns:assert (m.word(0xccdd) if name=='atoi' else m.long(0xccdd))==(65536-42 if name=='atoi' else 0x100000000-42)
   done(m,'invalid_lvalue_return_or_stop')
 for name in ('atoi','atol'):
  m=Machine(images,bytes([140,0,141 if name=='atoi' else 142,0]));m.u.mem_write(0x5000*16+0x40,b'far -42\0'+b'R'*73);m.invoke(name)
  assert (m.word(0xd482) if name=='atoi' else m.long(0xd582))==(65536-42 if name=='atoi' else 0x100000000-42)
  assert m.word(DATA['pending_near'])==0;done(m,'actual_far_source')
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nCONVERT >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_conversions.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[]
 for unit in manifest['units']:
  code=(OUT/unit['name']).read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
 assert [sha((OUT/f'conversions{i}.bin').read_bytes()) for i in (1,2)]==EXPECTED
 records,groups,coverage=suite(images);optional=None
 expected_instructions={int(a,16) for a in re.findall(r'^convert_loc_([0-9a-f]+):',(ROOT/'src/aspect/conversions.asm').read_text(),re.M)}
 assert coverage==expected_instructions,(expected_instructions-coverage,coverage-expected_instructions)
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_conversion_bytes=218,paired_cpu_scenarios=len(records),all_component_ranges=len(images))
 summary=dos_test()
 report=dict(passed=True,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'CONVERT.EXE').read_bytes()),check_sha256=sha(Path(__file__).read_bytes()),
  inherited_checker_sha256={p:sha((ROOT/'standalone'/p).read_bytes()) for p in ['check_aspect_string_commands.py','check_aspect_strings.py','check_aspect_operands.py','check_aspect_flow.py']},
  original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Four actual conversion commands/scanner with actual CRT and native string/numeric/lvalue/near-far copy. File,builtin,invalid/error,unavailable-float callbacks controlled; no complete VM or arbitrary-bytecode safety. Native unchecked indexes and wrap retained; scanner flag permits dot but CRT decimal parser remains integer.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
