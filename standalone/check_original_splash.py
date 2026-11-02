#!/usr/bin/env python3
"""Replay the linked startup display; optional genuine 2.01 layout oracle."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--original',type=Path)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
m=DosImage(a.terminal,a.terminal.parent/'terminal.map');u=m.uc;cursor=[0,0];waits=[]
def interrupt(u,n,_):
 ax=u.reg_read(UC_X86_REG_AX);bx=u.reg_read(UC_X86_REG_BX);dx=u.reg_read(UC_X86_REG_DX)
 if n==0x16:
  assert ax==0;waits.append(bytes(u.mem_read(0xb8000,4000)));return
 assert n==0x10,(n,ax)
 if ax==3:u.mem_write(0xb8000,b'\x20\x07'*2000)
 elif ax==0x0600:
  assert dx==0x184f;u.mem_write(0xb8000,bytes([32,bx>>8])*2000)
 elif ax>>8==2:cursor[:]=[dx>>8,dx&255]
 elif ax>>8==9:
  row,col=cursor;assert row<25 and col<80
  u.mem_write(0xb8000+2*(row*80+col),bytes([ax&255,bx&255]))
 else:raise AssertionError(('unexpected BIOS',hex(ax)))
u.hook_add(UC_HOOK_INTR,interrupt)
sp=m.offset('terminal_stack_top')-4
u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.code_segment))
for reg,value in [(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_ES,0x1357)]:u.reg_write(reg,value)
entry=m.symbols['terminal_special_splash'];u.reg_write(UC_X86_REG_CS,entry>>4)
u.emu_start(entry,0,count=100000)
assert m.returned and len(waits)==1 and u.reg_read(UC_X86_REG_SP)==sp+4
assert u.reg_read(UC_X86_REG_DS)==m.ds and u.reg_read(UC_X86_REG_BP)==0xbabe and u.reg_read(UC_X86_REG_ES)==0x1357
screen=waits[0];cells=list(struct.unpack('<2000H',screen))
for row in range(25):
 for col in range(80):
  if row not in (10,11,12,14,17,18,19,22):
   want=(0x5fdf if col<12 else 0x0fdf) if row in (0,2,4,6,8) and col>=6 else 0x5f20
   assert cells[row*80+col]==want,(row,col)
def text(row,col,value,attr):
 pos=2*(row*80+col);assert screen[pos:pos+len(value)*2]==b''.join(bytes([c,attr]) for c in value)
text(14,31,b'Intuitive Communications (r)',13)
text(17,36,b'Version 2.01-LoC.3',15)
text(18,36,b'LoC SPECIAL EDITION',15)
text(19,31,b'LoSs oF CoNtRoL / Sysop: bstar',15)
reference=False
if a.original:
 b=a.original.read_bytes();assert hashlib.sha256(b).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 base=0x25950
 for at in range(0x5f36,0x5f4e,6):
  pos,attrptr,string=struct.unpack_from('<HHH',b,base+at);value=b[base+string:].split(b'\0')[0]
  text(pos>>8,pos&255,value,struct.unpack_from('<H',b,base+attrptr)[0])
 reference=True
(a.output/'screen.bin').write_bytes(screen)
(a.output/'result.json').write_text(json.dumps(dict(passed=True,terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),original_layout_compared=reference,scope='Actual linked8086 splash with modeled BIOS, original logo/tagline positions and attributes, stripe geometry, edition lines and far-return/register ownership. Not physical video acceptance.'),indent=2)+'\n')
print('PASS linked original splash layout, edition lines, BIOS wait and register/stack restoration; original oracle:',reference)
