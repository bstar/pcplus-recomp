#!/usr/bin/env python3
"""Source-only native baud getter CPU checks; optional original byte comparison."""
import argparse,hashlib,json,random,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_SP,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_EFLAGS
ROOT=Path(__file__).resolve().parents[1]
RATES=[300,1200,2400,4800,9600,19200,38400,57600,115200]
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 source=ROOT/'src/aspect/directory_builtins.asm';binary=out/'baud.bin'
 subprocess.run(['nasm','-fbin','-DASPECT_DIRECTORY_FLAT','-DASPECT_DIRECTORY_UNIT=3',str(source),'-o',str(binary)],check=True)
 code=binary.read_bytes();assert code==bytes.fromhex('8b1e7ee6d1e3d1e38b8770328b977232c3')
 native=None
 if a.original:
  image=a.original.read_bytes();assert sha(a.original)==ORIGINAL
  manifest=json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())
  code_overlay=next(o for o in manifest['overlays'] if o['id']==16);data_overlay=next(o for o in manifest['overlays'] if o['id']==32)
  offset=code_overlay['source_file_offset']+0xda59-code_overlay['relative_load_segment']*16
  table=data_overlay['source_file_offset']+0x3270
  assert image[offset:offset+17]==code and image[table:table+36]==struct.pack('<9I',*RATES)
  native=dict(code_file_offset=offset,table_file_offset=table,code_bytes=17,table_bytes=36,original_sha256=ORIGINAL)
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x1da59,code)
 rng=random.Random(0xDA59);count=0
 for rates in [RATES]+[[rng.randrange(0x100000000) for _ in RATES] for _ in range(32)]:
  u.mem_write(0x43270,struct.pack('<9I',*rates))
  for index,value in enumerate(rates):
   u.mem_write(0x4e67e,struct.pack('<H',index));u.mem_write(0x48000,struct.pack('<H',0x100))
   preserved={UC_X86_REG_BP:rng.randrange(65536),UC_X86_REG_SI:rng.randrange(65536),UC_X86_REG_DI:rng.randrange(65536),UC_X86_REG_CS:0x1000,UC_X86_REG_DS:0x4000,UC_X86_REG_SS:0x4000}
   for reg,v in preserved.items():u.reg_write(reg,v)
   u.reg_write(UC_X86_REG_SP,0x8000);u.reg_write(UC_X86_REG_EFLAGS,0x602)
   u.emu_start(0x1da59,0x10100,count=20)
   assert u.reg_read(UC_X86_REG_AX)|(u.reg_read(UC_X86_REG_DX)<<16)==value
   assert u.reg_read(UC_X86_REG_BX)==index*4 and u.reg_read(UC_X86_REG_SP)==0x8002
   assert all(u.reg_read(reg)==v for reg,v in preserved.items()) and u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x600
   assert bytes(u.mem_read(0x43270,36))==struct.pack('<9I',*rates) and bytes(u.mem_read(0x4e67e,2))==struct.pack('<H',index)
   count+=1
 result=dict(passed=True,cpu_cases=count,source_sha256=sha(source),checker_sha256=sha(Path(__file__)),binary_sha256=sha(binary),original_inputs=[str(a.original)] if a.original else [],original_comparison=native,rates=RATES,scope=__doc__+' Exact17-byte native routine,9 valid selectors over33 independent tables, full32-bit result, DS=SS/near return and preserved registers/IF/DF. Native indexing is unchecked; maintained runtime bounds and full application are separate tests.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',count,'native getter CPU cases; original comparison',bool(native))
if __name__=='__main__':main()
