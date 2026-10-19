#!/usr/bin/env python3
"""Check exact resident long arithmetic against independent integer expectations."""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX as AX,UC_X86_REG_BX as BX,UC_X86_REG_CX as CX,UC_X86_REG_DX as DX,UC_X86_REG_SI as SI,UC_X86_REG_DI as DI,UC_X86_REG_BP as BP,UC_X86_REG_SP as SP,UC_X86_REG_CS as CS,UC_X86_REG_DS as DS,UC_X86_REG_SS as SS
from build_aspect_long import ROOT,OUT,UNITS,sha,vectors
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EXPECTED=['162fc5e02b25028fc22d2e8abe73b59ec98a48ea0fff5c486ee019b883140bb1','9db02483f8a2984043fad60a7ad569bb980650f69e03a9b538dcfc93472026f2','aabb59ae701ca960c7d29a60395b2af2be588a8a1eef141fc84b74bd2b7ac760','e772eee5eba8f85dd90f45ac45a76df2b732bf71ec9aed45ca76977088bccf29','f967ebbb7331d9fc3bcd580b2874eaa3a792dc31cfa18b31676ba46554219838','78f759f45b4087e0ec097caa5ad22d702b192bd5fa877101449c2089e82f54e1','6016756336e849d5edbf7d95ec25ce0ed33fca1b73a0981b604264a8526341db','fe6735f84daa98a5a3a6096f6aec63f1a0fcd3b35e8e3fdecd55c52fb8ac3d96','662c3961a18fa3b1f8cd982d948e034393c452a15b6820392110491e472c1cab','c519f466ee3ec630280945a7d9b5767acddab0c9c66f195a70fb6c46c6395816']
class Machine:
 def __init__(self,units):
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000)
  for start,data in units:self.uc.mem_write(0x20000+start,data)
  self.visited=set();self.interrupts=[]
  self.uc.hook_add(UC_HOOK_CODE,lambda uc,addr,size,user:self.visited.add(addr-0x20000))
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,user):self.interrupts.append(number);uc.emu_stop()
 def run(self,name,a,b):
  uc=self.uc;uc.reg_write(CS,0x2000);uc.reg_write(DS,0x1000);uc.reg_write(SS,0x1000)
  for reg,value in [(BP,0xabcd),(BX,0x1234),(SI,0x5678),(DI,0x9abc),(SP,0xe000),(AX,a&65535),(DX,a>>16),(CX,b&65535)]:uc.reg_write(reg,value)
  uc.mem_write(0x12000,struct.pack('<I',a));words=[0xff00]
  if name.endswith('_value'):
   if 'shift' not in name:words+=[a&65535,a>>16,b&65535,b>>16]
  else:
   words+=[0x2000,b&65535]
   if 'shift' not in name:words+=[b>>16]
  uc.mem_write(0x1e000,struct.pack('<'+'H'*len(words),*words));self.interrupts=[]
  start=next(s for n,s,e in UNITS if n==name);uc.emu_start(0x20000+start,0x2ff00,count=20000)
  if self.interrupts:return None,list(self.interrupts)
  assert uc.reg_read(SP)==0xe000+len(words)*2,(name,'SP')
  assert all(uc.reg_read(r)==v for r,v in [(BP,0xabcd),(BX,0x1234),(SI,0x5678),(DI,0x9abc),(DS,0x1000),(SS,0x1000)]),(name,'ABI')
  value=(uc.reg_read(AX)|(uc.reg_read(DX)<<16)) if name.endswith('_value') else struct.unpack('<I',uc.mem_read(0x12000,4))[0]
  return value,[]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);args=p.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_long.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());units=[];native=[]
 original=args.original.read_bytes() if args.original else None
 if original:assert sha(args.original)==ORIGINAL
 for unit,expected in zip(manifest['units'],EXPECTED):
  path=OUT/(unit['name']+'.bin');assert sha(path)==unit['sha256']==expected
  units.append((unit['start'],path.read_bytes()))
  if original:
   block=original[unit['source_file_start']:unit['source_file_start']+unit['bytes']];assert block==path.read_bytes();native.append((unit['start'],block))
 machines=[Machine(units)]+([Machine(native)] if native else []);count=0
 for op,a,b,value in vectors():
  for name in [op,op+'_value']:
   for machine in machines:assert machine.run(name,a,b)==(value,[]),(name,hex(a),hex(b),hex(value))
   count+=1
 expected_addresses={int(a,16) for a in re.findall(r'^\.L([0-9a-f]+):',(ROOT/'src/aspect/long_arithmetic.asm').read_text(),re.M)}
 assert machines[0].visited==expected_addresses,(len(machines[0].visited),len(expected_addresses))
 for name in ['divide','modulo','divide_value','modulo_value']:
  # A stopped CPU exception leaves Unicorn's pending-fault state; isolate faults.
  for blocks in [units]+([native] if native else []):assert Machine(blocks).run(name,1,0)==(None,[0]),name
  count+=1
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nLONG >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 for name in ['DONE.TXT','PASS.TXT','FAIL.TXT']:(OUT/name).unlink(missing_ok=True)
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 summary=(OUT/'DONE.TXT').read_text().strip();assert summary==f'ASPECT_LONG {manifest["DOS_checks"]} checks 0 failures',summary
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 report=dict(passed=True,cpu_scenarios=count,instruction_addresses=len(machines[0].visited),DOS_summary=summary,binary_sha256=sha(OUT/'LONG.EXE'),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__).resolve()),vectors_sha256=sha(OUT/'VECTORS.BIN'),result_sha256=sha(OUT/'RESULT.TXT'),original_inputs=[] if not original else [str(args.original)],optional_original=None if not original else dict(original_sha256=ORIGINAL,exact_bytes=manifest['bytes'],paired_cpu_scenarios=count),scope='Exact535-byte resident long arithmetic, real instructions with independent signed/wrapping expectations. Direct zero divisor CPU INT0 observed; zero divisors excluded from actual DOS suite. All shifts use native one-bit loops and low-byte counts.')
 (OUT/('checks-native.json' if original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
