#!/usr/bin/env python3
"""Native strings CPU/DOS component checks; optional private original comparison.

Actual maintained numeric/frame/read/near/far-copy code executes. CRT, builtin
and invalid/error callbacks are explicit fixtures, not replacement string code.
"""
import argparse,json,os,shutil,struct,subprocess,time
from pathlib import Path
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SP,UC_X86_REG_IP,
 UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS)
from check_aspect_operands import Machine as OperandMachine,CS,DS,STACK,STOP,TOKEN,BUFFER
from build_aspect_strings import ROOT,OUT,SHA,FILE_BASE,UNITS,ENTRIES,OPERAND_UNITS,FLOW_UNITS,TRANSFORM,sha
DATA=dict(bank=0xd13a,globals=0xdb82,pending_far=0xdd82,pending_near=0xdd86,
 scratch=0xdd88,scratch_pointer=0xe104,scratch_index=0xe106,transform=0x7748,
 check_range=0xe37c,exit_state=0xe378)
BUILTIN=0x5100

def encode(text,position,line):
 stride=((position+line)&0xffffffff)%12+1;parity=position&1
 d=[-b if (i+parity)&1 else b for i,b in enumerate(TRANSFORM)]
 return bytes([(len(text)+0xb3)&255,(parity<<7)|(len(text)+stride)]+[(b+d[((i+1)*stride)%13])&255 for i,b in enumerate(text)])

class Machine(OperandMachine):
 def __init__(self,images,data=b'',buffered=0):
  super().__init__(images,data,buffered)
  self.string_calls=[];self.string_errors=[];self.string_error_returns=True;self.string_builtin_index=None
  self.put(DATA['pending_near'],0);self.put(DATA['scratch_index'],0);self.put(DATA['check_range'],1);self.put(DATA['exit_state'],0)
  self.u.mem_write(DS*16+DATA['pending_far'],bytes(4));self.u.mem_write(DS*16+DATA['scratch'],b'\xa5'*891)
  self.u.mem_write(DS*16+DATA['transform'],TRANSFORM);self.u.mem_write(DS*16+BUILTIN,b'BUILTIN\0'+b'Q'*73)
  for i in range(128):
   self.put(DATA['globals']+i*4,0x40);self.put(DATA['globals']+i*4+2,0x5000+i*16)
   self.u.mem_write((0x5000+i*16)*16+0x40,bytes((j*13+i)&255 for j in range(81)))
 def near(self,o,n):return bytes(self.u.mem_read(DS*16+o,n))
 def far(self,i):return bytes(self.u.mem_read((0x5000+i*16)*16+0x40,81))
 def write(self,o,b):self.u.mem_write(DS*16+o,b)
 def on_code(self,cpu,address,size,_):
  ip=address-CS*16
  if ip not in (0x845a,0xda83,0x4efb):return super().on_code(cpu,address,size,_)
  sp=cpu.reg_read(UC_X86_REG_SP);args=[self.word(sp+i) for i in (2,4,6,8)];value=cleanup=0
  if ip==0x845a:
   dest,width,count,token=args;assert token==TOKEN and width in (1,4)
   if width==4:return super().on_code(cpu,address,size,_)
   self.string_calls.append(('fread',count));pos=self.position();chunk=self.data[pos:pos+count]
   if chunk:self.write(dest,bytes(chunk))
   self.set_position(pos+len(chunk));value=len(chunk)
  elif ip==0xda83:
   self.string_builtin_index=args[0];self.string_calls.append(('builtin',args[0]));value=BUILTIN;cleanup=2
  else:
   assert args[0]==1;self.string_errors.append(1);cleanup=2
   if not self.string_error_returns:self.aborted=True;cpu.emu_stop();return
  cpu.reg_write(UC_X86_REG_AX,value);cpu.reg_write(UC_X86_REG_IP,self.word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def invoke(self,name,*args):
  self.reached=self.aborted=False;self.write(STACK-128,b'\xa5'*144)
  self.write(STACK,struct.pack('<'+'H'*(len(args)+1),STOP,*args))
  for reg,v in [(UC_X86_REG_SP,STACK),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1357),(UC_X86_REG_DI,0x2468)]:self.u.reg_write(reg,v)
  target=ENTRIES.get(name,0x9286 if name=='far_copy' else 0x76b0)
  self.u.emu_start(CS*16+target,0,count=100000)
  if not self.aborted:
   assert self.reached and self.u.reg_read(UC_X86_REG_SP)==STACK+2+(0 if name=='far_copy' else len(args)*2)
   assert self.u.reg_read(UC_X86_REG_BP)==0xabcd and self.u.reg_read(UC_X86_REG_SI)==0x1357 and self.u.reg_read(UC_X86_REG_DI)==0x2468
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DS
  assert not self.u.reg_read(UC_X86_REG_EFLAGS)&0x400
  for a,b,code in self.images:assert bytes(self.u.mem_read(CS*16+a,b-a))==code
  return self.u.reg_read(UC_X86_REG_AX)
 def record(self):
  return dict(position=self.position(),errors=self.string_errors,invalids=self.invalids,aborted=self.aborted,
   calls=self.string_calls,scratch_index=self.word(DATA['scratch_index']),pending_near=self.word(DATA['pending_near']),
   near_digest=sha(self.near(DATA['scratch'],891)),far_digest=sha(b''.join(self.far(i) for i in range(3))))

def suite(images):
 records=[];groups={}
 def done(m,g):records.append(m.record());groups[g]=groups.get(g,0)+1
 for n in range(1,81):
  for parity in range(2):
   for line in range(12):
    text=bytes((i*73+n)%255+1 for i in range(n));wire=encode(text,parity,line)
    m=Machine(images,wire);p=m.invoke('read_literal');assert m.near(p,n+1)==text+b'\0' and m.position()==n+2;done(m,'literal_all_lengths_strides_parities')
 m=Machine(images)
 for i in range(44):assert m.invoke('next_scratch')==DATA['scratch']+81*(i%11) and m.word(DATA['scratch_index'])==(i+1)%11
 done(m,'scratch_rotation')
 for initial in [11,12,65535]:
  m=Machine(images);m.put(DATA['scratch_index'],initial);p=m.invoke('next_scratch');assert p==(DATA['scratch']+81*initial)&65535 and m.word(DATA['scratch_index'])==((initial+1)&65535)%11;done(m,'unchecked_scratch_initial_index')
 for index in [0,1,2,31,127]:
  for flag in [0,1,2]:
   m=Machine(images);before=m.far(index);p=m.invoke('read_global',flag,index);assert m.near(p,81)==before
   assert m.word(DATA['pending_near'])==(p if flag else 0)
   changed=bytes((i*7+19)&255 for i in range(81));m.write(p,changed);m.invoke('flush')
   assert m.far(index)==(changed if flag else before) and m.word(DATA['pending_near'])==0
   m.invoke('flush');done(m,'far_global_read_writeback')
 for token in range(256):
  if token in [100,110,140,150,160,170]:continue
  m=Machine(images,bytes([token]));p=m.invoke('read');assert p==0xccdd and m.invalids==1;done(m,'invalid_selectors')
 for token in [100,110,140,150,160]:
  m=Machine(images,bytes([token,2,0]));m.set('frame',0x6000);p=m.invoke('read')
  assert p==({100:DATA['bank']+162,110:BUILTIN,140:DATA['scratch'],150:0x5ffe,160:0x6002}[token]);done(m,'valid_selectors')
 for check in [0,1]:
  for exit_state in [0,1]:
   for value in [-1,0,1,79,80,81,32767,-32768]:
    m=Machine(images,b'\xab'+struct.pack('<H',value&65535));m.put(DATA['check_range'],check);m.put(DATA['exit_state'],exit_state)
    p=m.invoke('length_operand');bad=check and not 0<=value<=80
    assert len(m.string_errors)==bool(bad) and p==(0 if bad and exit_state else value&65535);done(m,'bounded_length_return_policy')
 for value in [0,1,2,255,65535]:
  m=Machine(images,bytes([value]) if value<256 else b'');assert m.invoke('option_flag')==int(value==1);done(m,'option_flag')
 for count in [0,1,2,79,80]:
  for global_destination in [False,True]:
   data=bytes([140 if global_destination else 100,0,110,0,1,171,count,0]);m=Machine(images,data)
   m.write(DATA['bank'],b'D'*81);m.write(BUILTIN,b'S'*81);before=m.far(0);m.invoke('assign')
   actual=m.far(0) if global_destination else m.near(DATA['bank'],81)
   assert actual[:count]==b'S'*count and actual[count]==0 and actual[count+1:]==(before if global_destination else b'D'*81)[count+1:];done(m,'bounded_assignment')
 for option in [0,2,255]:
  m=Machine(images,bytes([100,0,110,0,option]));m.write(BUILTIN,b'S'*81);m.invoke('assign');assert m.near(DATA['bank'],81)==b'S'*80+b'\0';done(m,'default_assignment_count')
 # Original read ignores short fread return; leftover scratch bytes are decoded.
 m=Machine(images,encode(b'ABCDE',0,2)[:4]);p=m.invoke('read_literal');assert m.position()==4 and m.near(p,2)==b'AB' and m.near(p+5,1)==b'\0';done(m,'short_read_native_quirk')
 m=Machine(images,b'\xab\x51\0');m.string_error_returns=False;m.invoke('length_operand');assert m.aborted and m.string_errors==[1];done(m,'error_stop')
 m=Machine(images,b'\x63');m.invalid_returns=False;m.invoke('read');assert m.aborted and m.invalids==1;done(m,'invalid_stop')
 for n in [0,1,80,81]:
  m=Machine(images);m.u.mem_write(0x70000,b'F'*81);m.invoke('far_copy',0x7000,0,0x7100,0,n);assert bytes(m.u.mem_read(0x71000,n))==b'F'*n;done(m,'far_copy_lengths')
 return records,groups

def dos_test():
 folder=OUT/('dos-'+str(time.time_ns()));folder.mkdir();shutil.copy2(OUT/'STRINGS.EXE',folder/'STRINGS.EXE')
 config=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nSTRINGS >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 summary=(folder/'DONE.TXT').read_text().strip();assert (folder/'PASS.TXT').exists() and summary.endswith('0 failures'),(folder/'RESULT.TXT').read_text()
 return dict(summary=summary,folder=str(folder.relative_to(ROOT)),binary_sha256=sha((folder/'STRINGS.EXE').read_bytes()))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);args=p.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_strings.py')],check=True,stdout=subprocess.DEVNULL)
 images=[(a,b,(OUT/('strings-'+n+'.bin')).read_bytes()) for _,n,a,b,_ in UNITS]
 images += [(a,b,(OUT/('operands-'+n+'.bin')).read_bytes()) for _,n,a,b in OPERAND_UNITS]
 images += [(a,b,(OUT/('flow-'+n+'.bin')).read_bytes()) for _,n,a,b in FLOW_UNITS]
 images += [(0xd0d0,0xd195,(OUT/'stack.bin').read_bytes()),(0x85b4,0x85fc,(OUT/'copy.bin').read_bytes())]
 records,groups=suite(images);optional=None
 if args.original:
  original=args.original.read_bytes();assert sha(original)==SHA;paired=[]
  for unit,name,a,b,base in UNITS:
   raw=original[base+a:base+b];assert raw==images[unit-1][2];paired.append((a,b,raw))
  native,ng=suite(paired+images[len(UNITS):]);assert native==records and ng==groups
  optional=dict(sha256=SHA,exact_string_bytes=sum(b-a for _,_,a,b,_ in UNITS),identical_cpu_records=len(records))
 data=(json.dumps(records,sort_keys=True,separators=(',',':'))+'\n').encode();(OUT/'cpu-records.json').write_bytes(data)
 dos=dos_test();report=dict(passed=True,original_inputs=[] if args.original is None else [str(args.original)],manifest_sha256=sha((OUT/'manifest.json').read_bytes()),inherited_checker_sha256=sha((ROOT/'standalone/check_aspect_operands.py').read_bytes()),inherited_flow_checker_sha256=sha((ROOT/'standalone/check_aspect_flow.py').read_bytes()),cases=len(records),groups=groups,DOS=dos,optional_original=optional,records_sha256=sha(data),harness_sha256=sha(Path(__file__).read_bytes()),sources=json.loads((OUT/'manifest.json').read_text())['sources'],scope='617 native string bytes plus native numeric/frame/near/far-copy helpers; explicit CRT,builtin,error fixtures. Short fread is unchecked, scratch/index arithmetic unchecked. No whole VM or builtin system integration claim.')
 (OUT/('checks-native.json' if args.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))
if __name__=='__main__':main()
