#!/usr/bin/env python3
"""Source-only CPU and actual8086 DOS checks for exact directory getter module."""
import argparse,json,os,random,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_directory import ROOT,OUT,SOURCE,sha
OFFSETS=[61,95,86,0,105,25,75,52]
NAMES=['ldate','kbdfile','metakey','name','note','phone','pword','script']
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'

def cpu():
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 u.mem_write(0x1d9b5,(OUT/'unit1.bin').read_bytes());u.mem_write(0x1daa2,(OUT/'unit2.bin').read_bytes())
 u.hook_add(UC_HOOK_CODE,lambda m,a,s,d:m.emu_stop() if a==0x1f000 else None)
 def intr(*args):raise AssertionError('No modeled interrupts allowed')
 u.hook_add(UC_HOOK_INTR,intr);rng=random.Random(201);count=0
 for entry,value,pointer in [(0xdaa2+4*i,None,0xe650+n) for i,n in enumerate(OFFSETS)]+[(0xd9b5,rng.randrange(65536),None) for _ in range(2048)]:
  for reg,val in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SP,0xd000),(UC_X86_REG_BP,0xc000),(UC_X86_REG_BX,0x4321),(UC_X86_REG_CX,0x8765),(UC_X86_REG_DX,0xabcd),(UC_X86_REG_SI,0x9876),(UC_X86_REG_DI,0x5432),(UC_X86_REG_EFLAGS,0xad7)]:u.reg_write(reg,val)
  u.mem_write(0x4d000,struct.pack('<H',0xf000));u.mem_write(0x4e482,struct.pack('<H',value or 0));before=bytes(u.mem_read(0x4e482,2))
  u.emu_start(0x10000+entry,0x20000,count=8)
  assert u.reg_read(UC_X86_REG_IP)==0xf000
  assert u.reg_read(UC_X86_REG_AX)==(pointer if pointer is not None else value)
  for reg,val in [(UC_X86_REG_SP,0xd002),(UC_X86_REG_BP,0xc000),(UC_X86_REG_BX,0x4321),(UC_X86_REG_CX,0x8765),(UC_X86_REG_DX,0xabcd),(UC_X86_REG_SI,0x9876),(UC_X86_REG_DI,0x5432),(UC_X86_REG_EFLAGS,0xad7)]:assert u.reg_read(reg)==val
  assert bytes(u.mem_read(0x4e482,2))==before;count+=1
 return count

def dos():
 text=['BITS 16','CPU 8086','SEGMENT _TEXT public class=CODE use16','global _start','_start:',' mov ax,DGROUP',' mov ds,ax']
 for i,(name,offset) in enumerate(zip(NAMES,OFFSETS)):
  text+=['extern aspect_directory_builtin_'+name,f' mov byte [aspect_directory_record+{offset}],{65+i}',' call aspect_directory_builtin_'+name,f' cmp ax,aspect_directory_record+{offset}',' jne fail',' mov bx,ax',f' cmp byte [bx],{65+i}',' jne fail']
 text+=['extern aspect_directory_builtin_entry']
 for value in [0,1,7,200,32767,32768,65534,65535]:
  text += [f' mov word [aspect_directory_entry],{value}',' call aspect_directory_builtin_entry',f' cmp ax,{value}',' jne fail']
 text+=[' mov dx,success',' mov ah,9',' int 0x21',' mov ax,0x4c00',' int 0x21','fail:',' mov dx,failure',' mov ah,9',' int 0x21',' mov ax,0x4c01',' int 0x21','SEGMENT _DATA public class=DATA use16','GROUP DGROUP _DATA STACK','global aspect_directory_record,aspect_directory_entry','aspect_directory_record: times 114 db 0','aspect_directory_entry: dw 0',"success: db 'DIRECTORY16 PASS',13,10,'$'","failure: db 'DIRECTORY FAIL',13,10,'$'",'SEGMENT STACK stack class=STACK use16',' resb 1024']
 source=OUT/'diagnostic.asm';source.write_text('\n'.join(text)+'\n')
 subprocess.run(['nasm','-f','obj',str(source),'-o',str(OUT/'diagnostic.obj')],check=True)
 subprocess.run(['wlink','system','dos','option','quiet','option','start=_start','name',str(OUT/'DIRBUILT.EXE'),'file',str(OUT/'diagnostic.obj')+','+str(OUT/'directory.obj')],check=True)
 conf=OUT/'dosbox.conf';conf.write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nDIRBUILT >RESULT.TXT\nexit\n')
 (OUT/'RESULT.TXT').unlink(missing_ok=True)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(conf)],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=20)
 assert (OUT/'RESULT.TXT').read_bytes()==b'DIRECTORY16 PASS\r\n'
 return 16

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args()
 native=[]
 if a.original:
  image=a.original.read_bytes();assert __import__('hashlib').sha256(image).hexdigest()==ORIGINAL
  overlay=next(o for o in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if o['id']==16)
  for unit,entry,length in [(1,0xd9b5,4),(2,0xdaa2,32)]:
   offset=overlay['source_file_offset']+entry-overlay['relative_load_segment']*16
   assert image[offset:offset+length]==(OUT/f'unit{unit}.bin').read_bytes();native.append(dict(unit=unit,file_offset=offset,bytes=length))
 report=dict(passed=True,original_inputs=[str(a.original)] if a.original else [],source_sha256=sha(SOURCE),checker_sha256=sha(Path(__file__)),builder_sha256=sha(ROOT/'standalone/build_aspect_directory.py'),manifest_sha256=sha(OUT/'manifest.json'),cpu_cases=cpu(),dos_cases=dos(),original_comparison=native)
 report.update(binary_sha256=sha(OUT/'DIRBUILT.EXE'),scope='Exact36 native getter bytes,2056 CPU register/flag/return and16 actual8086 DOS relocation/record checks. No dispatcher, application loader, private record or UART IO.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Directory getters:',report['cpu_cases'],'CPU and',report['dos_cases'],'DOS PASS')
if __name__=='__main__':main()
