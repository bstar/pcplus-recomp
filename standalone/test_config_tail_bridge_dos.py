#!/usr/bin/env python3
"""Compare both bridge frames against compiled C callees in actual DOS8086."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 seeds=[0,1,0x7fff,0x8000,0xffff]+[(i*7919+3251)&65535 for i in range(95)]
 c=['unsigned calls,observed_cs,observed_ds,observed_ss;',
  'static unsigned code(void);', '#pragma aux code = "mov ax,cs" value [ax] modify [];',
  'static unsigned data(void);', '#pragma aux data = "mov ax,ds" value [ax] modify [];',
  'static unsigned stack(void);', '#pragma aux stack = "mov ax,ss" value [ax] modify [];',
  'static void touch(unsigned *p){*p=0xbeef;}']
 asm=['BITS 16','CPU 8086','%include "far_bridge.inc"','SEGMENT _TEXT public class=CODE use16','extern _bad_slots']
 for n in range(11):
  args=','.join('unsigned a'+str(i)for i in range(n))or'void'
  c+=['unsigned long __cdecl f'+str(n)+'_impl('+args+'){unsigned s=0x1234;',
   '++calls;observed_cs=code();observed_ds=data();observed_ss=stack();']
  for i in range(n):c+=['s=(unsigned)(s+a'+str(i)+'*'+str(i+1)+');']
  for i in range(n):c+=['touch(&a'+str(i)+');']
  c+=['return '+hex(0x60000000+(n<<16))+'UL|s;}']
  # Both adapters target the same real C function. The original wrapper is
  # a reference convention, not a generated expected return-value oracle.
  asm+=['NEAR_CDECL_TAIL_ENTRY _f'+str(n)+','+str(n),
   'NEAR_CDECL_ENTRY _g'+str(n)+','+str(n)]
  for mode in ('t','o'):
   name='_probe_'+mode+'_'+str(n)
   asm+=['global '+name,name+':','push bp','mov bp,sp','push bx','push si']
   for i in reversed(range(n)):asm+=['mov ax,[bp+4]','xor ax,'+str(((i+1)*0x1f13)&65535),'push ax']
   asm+=['call _'+('f'if mode=='t'else'g')+str(n),'mov bx,sp']
   for i in range(n):
    asm+=['mov si,[bp+4]','xor si,'+str(((i+1)*0x1f13)&65535),
     'cmp [ss:bx+'+str(i*2)+'],si','je .slot'+str(i),'inc word [_bad_slots]','.slot'+str(i)+':']
   asm+=['add sp,'+str(n*2),'pop si','pop bx','pop bp','ret']
 asm+=['SEGMENT PAD_CODE public align=16 class=PADCODE use16','times 65536 db 0',
  'SEGMENT ORACLE_CODE public align=16 class=FARCODE use16']
 for n in range(11):
  asm+=['FAR_CDECL_SHARED_ENTRY _f'+str(n)+','+str(n)+',oracle_shared_cdecl',
   'FAR_CDECL_ENTRY _g'+str(n)+','+str(n),'global _g'+str(n)+'_impl',
   '_g'+str(n)+'_impl:','jmp _f'+str(n)+'_impl']
 asm+=['FAR_CDECL_SHARED_BODY oracle_shared_cdecl']
 driver=['#include <stdio.h>','unsigned bad_slots;',
  'extern unsigned calls,observed_cs,observed_ds,observed_ss;',
  'static unsigned code(void);','#pragma aux code = "mov ax,cs" value [ax] modify [];',
  'static unsigned data(void);','#pragma aux data = "mov ax,ds" value [ax] modify [];',
  'static unsigned stack(void);','#pragma aux stack = "mov ax,ss" value [ax] modify [];',
  'static unsigned sp(void);','#pragma aux sp = "mov ax,sp" value [ax] modify [];']
 for n in range(11):
  for mode in ('t','o'):driver+=['extern unsigned long __cdecl probe_'+mode+'_'+str(n)+'(unsigned);']
 driver+=['static const unsigned seeds[100]={'+','.join(map(str,seeds))+'};','int main(void){unsigned i,before,after;unsigned long value;']
 for n in range(11):
  expected=[(0x60000000+(n<<16))|((0x1234+sum(((s^((i+1)*0x1f13))&65535)*(i+1)for i in range(n)))&65535)for s in seeds]
  driver+=['{static const unsigned long expected[100]={'+','.join(hex(v)+'UL'for v in expected)+'};',
   'for(i=0;i<100;++i){']
  for mode in ('t','o'):
   driver+=['before=sp();value=probe_'+mode+'_'+str(n)+'(seeds[i]);after=sp();',
    'if(after!=before||value!=expected[i]||bad_slots||observed_cs==code()||observed_ds!=data()||observed_ss!=stack()||data()!=stack()){',
    'printf("FAIL '+mode+' '+str(n)+' %u %lu %lu %u sp%u/%u cs%u/%u ds%u/%u ss%u/%u\\r\\n",i,value,expected[i],bad_slots,before,after,code(),observed_cs,data(),observed_ds,stack(),observed_ss);return 1;}']
  driver+=['}}']
 driver+=['if(calls!=2200)return 1;printf("PASS 2200\\r\\n");return 0;}']
 for name,lines in [('oracle.c',c),('bridges.asm',asm),('driver.c',driver)]:
  (out/name).write_text('\n'.join(lines)+'\n')
 subprocess.run(['nasm','-fobj','-I'+str(ROOT/'src/terminal')+'/',str(out/'bridges.asm'),'-o',str(out/'bridges.obj')],check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-od','-nt=ORACLE_CODE','-nc=FARCODE','-fo='+str(out/'oracle.obj'),str(out/'oracle.c')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fd=TAIL.lnk','-fm=TAIL.map','-fe=TAIL.EXE','driver.c','bridges.obj','oracle.obj'],cwd=out,check=True)
 response=out/'TAIL.lnk'
 response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname DATA clname BSS clname STACK\n')
 subprocess.run(['wlink','@TAIL.lnk'],cwd=out,check=True)
 (out/'CHECK.BAT').write_text('@echo off\nTAIL >CHECK.LOG\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
 (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
mount c "{out}"
c:
CHECK.BAT
exit
''')
 with(out/'dosbox.log').open('w')as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=25)
 text=(out/'CHECK.LOG').read_text();assert(out/'RESULT.TXT').read_text().strip()=='PASS'and'PASS 2200'in text,text
 result=dict(passed=True,calls=2200,argument_counts=list(range(11)),cpu='8086',sources={n:sha(ROOT/n)for n in ('standalone/test_config_tail_bridge_dos.py','src/terminal/far_bridge.inc')},
  binary_sha256=sha(out/'TAIL.EXE'),generated_sources={n:sha(out/n)for n in ('driver.c','oracle.c','bridges.asm')},
  scope='Both entry conventions, real C DX:AX returns, caller argument slots despite callee parameter writes, stack balance, separate CS and DS=SS. No hardware/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('DOS8086 tail/original bridge:2200 calls,0..10 argument words passed')


if __name__=='__main__':main()
