#!/usr/bin/env python3
"""Check reused native XLT/read policy; device/pattern/render services explicit."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,
 UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_EFLAGS)
from build_aspect_receive_policy import ROOT,OUT,SHA,UNITS,ENTRIES,sha
CS,DS,STACK,STOP=0x1000,0x3000,0xf000,0xf800
TABLE,COUNT,DISPLAY=0xd00a,0xe2f8,0xe37e
EXPECTED=['065fc1f8738e136d133e623777fecffd3554fa268a14c399b775b19c6d298fc1',
 '93cb24fd1411d027e85d590a5fa13b824093f97fa411e64b5ccfa34f4239038e']


class Machine:
 def __init__(self,images,kind=0):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.images=images
  for a,b,code in images:self.u.mem_write(CS*16+a,code)
  for reg,value in [(UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_ES,0x4321),(UC_X86_REG_EFLAGS,2)]:self.u.reg_write(reg,value)
  self.table=bytes(i if kind==0 else (17*i+3)&255 if kind==1 else 0 for i in range(256));self.write(TABLE,self.table+b'\xa6\x5a')
  self.trace=[];self.visits=set();self.reached=False
  self.u.hook_add(UC_HOOK_CODE,self.on_code);self.u.hook_add(UC_HOOK_INTR,self.interrupt)
 def put(self,o,v):self.write(o,struct.pack('<H',v&65535))
 def word(self,o):return struct.unpack('<H',self.u.mem_read(DS*16+o,2))[0]
 def write(self,o,b):self.u.mem_write(DS*16+o,b)
 def on_code(self,cpu,address,size,_):
  assert cpu.reg_read(UC_X86_REG_CS)==CS;ip=address-CS*16
  if ip==STOP:self.reached=True;cpu.emu_stop();return
  if any(a<=ip<b for a,b,_ in self.images):self.visits.add(ip);return
  assert ip in (0xaa65,0x5ca0,0x534e,0x610),hex(ip)
  sp=cpu.reg_read(UC_X86_REG_SP);cleanup=0
  if ip==0xaa65:value=self.raw;kind='R';ax=value
  elif ip==0x5ca0:value=self.delayed;kind='D';ax=value
  else:value=self.word(sp+2);assert value<=255;kind='P' if ip==0x534e else 'E';ax=0xa55a if kind=='P' else 0xb00b;cleanup=2 if kind=='P' else 0
  self.trace.append((kind,value))
  for reg,value in [(UC_X86_REG_AX,ax),(UC_X86_REG_BX,0xabcd),(UC_X86_REG_CX,0xcdef),(UC_X86_REG_DX,0xdef0),(UC_X86_REG_ES,0x5678)]:cpu.reg_write(reg,value)
  cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def interrupt(self,cpu,number,_):raise AssertionError(f'Unexpected interrupt {number}')
 def invoke(self,name,echo,delayed,monitor,raw,delayed_value=None):
  self.trace=[];self.visits=set();self.reached=False;self.raw=raw;self.delayed=raw if delayed_value is None else delayed_value
  self.put(COUNT,monitor);self.put(DISPLAY,echo);args=[delayed] if name=='displayed' else [echo,delayed]
  self.write(STACK-64,b'\xa5'*96);self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,value in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,value)
  self.u.emu_start(CS*16+ENTRIES[name],0,count=1000)
  assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+len(args)*2
  assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS and not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  assert bytes(self.u.mem_read(DS*16+TABLE,256))==self.table
  for a,b,code in self.images:assert bytes(self.u.mem_read(CS*16+a,b-a))==code
  return self.u.reg_read(UC_X86_REG_AX)


def suite(images):
 records=[];groups={};coverage=set()
 def one(m,name,echo,delayed,monitor,raw,mapped,group,delayed_value=None):
  value=m.invoke(name,echo,delayed,monitor,raw,delayed_value);assert value==mapped
  selected=raw if not delayed else raw if delayed_value is None else delayed_value
  expected=[('D' if delayed else 'R',selected)]
  if selected<32768:
   if monitor:expected.append(('P',mapped))
   if echo:expected.append(('E',mapped))
  assert m.trace==expected,(m.trace,expected)
  records.append(dict(name=name,echo=echo,delayed=delayed,monitor=monitor,raw=raw,result=value,trace=m.trace))
  groups[group]=groups.get(group,0)+1;coverage.update(m.visits)
 for kind in (0,1):
  m=Machine(images,kind)
  for value in range(256):
   for name in ENTRIES:
    for delayed in (0,1):
     for echo in (0,1):
      for monitor in (0,1):one(m,name,echo,delayed,monitor,value,m.table[value],'all_bytes_identity_nonidempotent_maps_once')
 m=Machine(images,2)
 for value in range(256):one(m,'read',1,0,1,value,0,'translated_nul_is_monitored_and_emitted')
 m=Machine(images,1)
 for value in (65535,65534,32768,32769,0xabcd):
  for name in ENTRIES:
   for delayed in (0,1,2,65535):
    for echo in (0,1,65535):
     for monitor in (0,1,65535):one(m,name,echo,delayed,monitor,value,value,'negative_words_bypass_all_services')
 for value,mapped in ((256,0xa6),(257,0x5a),(32767,0x77)):
  if value==32767:m.write((TABLE+value)&65535,bytes([mapped]))
  for name in ENTRIES:
   for delayed in (0,1):one(m,name,1,delayed,1,value,mapped,'unchecked_positive_word_index')
 for name in ENTRIES:
  for delayed in (0,1):one(m,name,1,delayed,1,17,m.table[23 if delayed else 17],'distinct_raw_delayed_sources',23)
 return records,groups,coverage


def dos_test():
 for name in ('DONE.TXT','PASS.TXT','FAIL.TXT'):(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nPOLICY >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=45)
 summary=(OUT/'DONE.TXT').read_text().strip();assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text();assert summary.endswith('0 failures'),summary;return summary


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path);args=parser.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_receive_policy.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());images=[];expected_instructions=set()
 for unit in manifest['units']:
  path=OUT/unit['name'];code=path.read_bytes();assert sha(code)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],code))
  assembly=subprocess.check_output(['ndisasm','-b','16','-o',hex(unit['start']),str(path)],text=True)
  expected_instructions.update(int(line.split()[0],16) for line in assembly.splitlines())
 assert [sha(code) for _,_,code in images]==EXPECTED
 policy_bytes=sum(b-a for a,b,_ in images);assert policy_bytes==manifest['native_policy_bytes']==83 and manifest['reused_native_bytes']==64
 records,groups,coverage=suite(images);assert coverage==expected_instructions,(expected_instructions-coverage,coverage-expected_instructions);optional=None
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;native=[]
  for unit in manifest['units']:
   a,b,base=unit['start'],unit['end_exclusive'],unit['file_base'];code=original[base+a:base+b];assert code==(OUT/unit['name']).read_bytes();native.append((a,b,code))
  assert suite(native)==(records,groups,coverage)
  optional=dict(original_sha256=SHA,exact_policy_bytes=policy_bytes,reused_native_bytes=64,paired_cpu_scenarios=len(records))
 summary=dos_test()
 report=dict(passed=True,native_policy_bytes=policy_bytes,reused_native_bytes=64,cpu_scenarios=len(records),groups=groups,DOS_summary=summary,optional_original=optional,
  binary_sha256=sha((OUT/'POLICY.EXE').read_bytes()),check_sha256=sha(Path(__file__).read_bytes()),original_inputs=[] if optional is None else [str(args.original)],visited_instructions=len(coverage),
  scope='Actual native receive policy reused from original source reconstruction, plus4C3C adapter. Explicit raw/delayed/pattern/render component callbacks. Nonidempotent maps prove exactly one lookup before pattern then renderer, negative bypass and native unchecked positive-word index retained. No complete renderer, event engine, UART or modem acceptance claim.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
