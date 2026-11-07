#!/usr/bin/env python3
"""Exact native clock units and CPU replay with explicit DOS/operand boundaries."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_context_help import ROOT,sha
DATA=0x40000

class Clock:
 def __init__(self,units,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.original=original is not None
  if original is not None:
   self.u.mem_write(0x10000,original[0x1200:0xe2d0])
   manifest=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())
   for r in manifest['overlays']:
    if r['id']==18:self.u.mem_write(0x10000+r['relative_load_segment']*16,original[r['source_file_offset']:r['source_file_offset']+r['initialized_bytes']])
    if r['id']==32:self.u.mem_write(DATA,original[r['source_file_offset']:r['source_file_offset']+r['initialized_bytes']])
  else:
   for r in units:self.u.mem_write(0x10000+r['start'],(ROOT/r['output']).read_bytes())
  for reg in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES):self.u.reg_write(reg,DATA>>4)
  self.u.reg_write(UC_X86_REG_CS,0x1000)
  for at,value in [(0x4729,b'%2.2d/%2.2d/%2.2d\0'),(0x4786,b'%02d:%02d:%02d%\0'),(0x4796,b'PM\0AM\0%02d:%02d:%02d%2s\0')]:self.u.mem_write(DATA+at,value)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def word(self,at):return struct.unpack('<H',self.u.mem_read(DATA+at,2))[0]
 def string(self,at):return bytes(self.u.mem_read(DATA+at,81)).split(b'\0')[0]
 def ret(self,value,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,value);self.u.reg_write(UC_X86_REG_IP,self.word(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def hook(self,u,at,size,_):
  self.seen.add(at)
  if at==0x1f800:u.emu_stop();return
  if at==0x1df0b:self.events.append('destination');self.ret(0x5800)
  elif at==0x1dd68:
   sp=u.reg_read(UC_X86_REG_SP);assert self.word(sp+2)==1 and self.word(sp+4)==0
   self.events.append('mode');self.ret(self.mode,4)
  elif at==0x1e0a4:self.events.append('flush');self.ret(0xbeef)
  elif not self.original and at in (0x18268,0x182b6):
   sp=u.reg_read(UC_X86_REG_SP);args=[self.word(sp+i*2) for i in range(1,7)];dest=args[0]
   if at==0x18268:text=self.string(args[1]);self.events.append('copy')
   elif args[1]==0x4729:
    assert args[2:5]==[self.month,self.day,(self.year-1900)&65535];text=f'{self.month:02}/{self.day:02}/{self.year-1900:02}'.encode()
   else:
    h=self.hour if self.mode else (self.hour%12 or 12);assert args[1]==(0x4786 if self.mode else 0x479c) and args[2:5]==[h,self.minute,self.second]
    if not self.mode:assert self.string(args[5])==(b'PM' if self.hour>=12 else b'AM')
    text=(f'{h:02}:{self.minute:02}:{self.second:02}'+('' if self.mode else 'PM' if self.hour>=12 else 'AM')).encode()
   u.mem_write(DATA+dest,text+b'\0');self.ret(dest if at==0x18268 else len(text))
 def kernel(self,u,number,_):
  assert number==0x21
  ah=u.reg_read(UC_X86_REG_AH);self.events.append('DOS'+hex(ah))
  if ah==0x2a:u.reg_write(UC_X86_REG_CX,self.year);u.reg_write(UC_X86_REG_DX,self.month*256+self.day)
  else:
   assert ah==0x2c;u.reg_write(UC_X86_REG_CX,self.hour*256+self.minute);u.reg_write(UC_X86_REG_DX,self.second*256+99)
 def run(self,kind,year=2026,month=11,day=6,hour=0,minute=0,second=0,mode=0):
  self.kind=kind;self.year=year;self.month=month;self.day=day;self.hour=hour;self.minute=minute;self.second=second;self.mode=mode;self.events=[];self.seen=set()
  self.u.mem_write(DATA+0x57f0,b'Z'*112);self.u.mem_write(DATA+0xd000,struct.pack('<H',0xf800))
  for reg,value in [(UC_X86_REG_SP,0xd000),(UC_X86_REG_BP,0xc000),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:self.u.reg_write(reg,value)
  self.u.emu_start(0x1e689 if kind=='date' else 0x1e909,0x20000,count=100000)
  assert self.u.reg_read(UC_X86_REG_IP)==0xf800 and self.u.reg_read(UC_X86_REG_SP)==0xd002
  assert self.u.reg_read(UC_X86_REG_BP)==0xc000 and self.u.reg_read(UC_X86_REG_SI)==0x1234 and self.u.reg_read(UC_X86_REG_DI)==0x5678
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
  text=self.string(0x5800);expected=(f'{month:02}/{day:02}/{year-1900:02}' if kind=='date' else f'{hour if mode else hour%12 or 12:02}:{minute:02}:{second:02}'+('' if mode else 'PM' if hour>=12 else 'AM')).encode();assert text==expected,(kind,text,expected)
  assert bytes(self.u.mem_read(DATA+0x57f0,16))==b'Z'*16 and bytes(self.u.mem_read(DATA+0x5800+len(text)+1,95-len(text)))==b'Z'*(95-len(text))
  assert self.events.count('destination')==self.events.count('flush')==1
  return text

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 fixture=ROOT/'standalone/fixtures/aspect_clock_native_units.json';proof=json.loads(fixture.read_text());units=[]
 for r in proof['units']:
  dest=out/(r['name']+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/','-DASPECT_CLOCK_FLAT','-DASPECT_CLOCK_UNIT='+str(r['unit']),str(ROOT/'src/aspect/clock_commands.asm'),'-o',str(dest)],check=True);assert sha(dest)==r['sha256'];units.append(dict(**r,output=str(dest.relative_to(ROOT))))
 for name,start,source,flags in [('date-format',0x36d4,'reconstruction/directory_accounting/date_original.asm',[]),('get-date',0x776e,'reconstruction/directory_accounting/getdate_original.asm',[]),('get-time',0x778c,'src/aspect/receive_commands.asm',['-DASPECT_RECEIVE_COMMANDS_FLAT','-DASPECT_RECEIVE_COMMANDS_UNIT=6'])]:
  dest=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',*flags,str(ROOT/source),'-o',str(dest)],check=True)
  expected=next(r for r in proof['reused_units'] if r['name']==name);assert sha(dest)==expected['sha256'] and dest.stat().st_size==expected['bytes']
  units.append(dict(**expected,output=str(dest.relative_to(ROOT))))
 original=a.original.read_bytes() if a.original else None
 if original is not None:assert hashlib.sha256(original).hexdigest()==proof['original_sha256']
 source=Clock(units);native=Clock(units,original) if original is not None else None;count=0;seen=set()
 cases=[dict(kind='date',year=y,month=m,day=d) for y in (1980,1999,2000,2026,2099) for m in (1,6,12) for d in (1,15,28)]
 cases += [dict(kind='time',hour=h,minute=m,second=s,mode=mode) for h in range(24) for m in (0,29,59) for s in (0,29,59) for mode in (0,1)]
 for case in cases:
  text=source.run(**case);seen|=source.seen
  if native is not None:assert native.run(**case)==text
  count+=1
 names=['src/aspect/clock_commands.asm','reconstruction/directory_accounting/date_original.asm','reconstruction/directory_accounting/getdate_original.asm','src/aspect/receive_commands.asm','reconstruction/uart/encodings.inc',str(fixture.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT))]
 report=dict(passed=True,cases=count,original_comparisons=count if native else 0,native_bytes=sum(r['bytes'] for r in units),new_native_bytes=171,units=units,instruction_addresses=len(seen),sources={n:sha(ROOT/n) for n in names},scope=__doc__+' Actual source handlers/clock helpers on DS=SS. DOS date/time, writable destination, bound operand and flush are explicit boundaries. Source formatter/strcpy modeled; optional original executes actual resident CRT and compares477 outcomes, including year-minus1900 and discarded trailing percent. Not actual DOS/VM/physical execution.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('CLOCK native',count,'cases;',report['original_comparisons'],'original comparisons')
if __name__=='__main__':main()
