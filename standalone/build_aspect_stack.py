#!/usr/bin/env python3
"""Build exact typed value-stack primitives and linked8086 DOS diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-stack'
START,END=0xd0d0,0xd195
SOURCE_FILE_START=109184
SHA='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
ENTRIES={'reserve':0xd0d0,'push_word':0xd0f2,'push_dword':0xd110,'push_eight':0xd134,
         'push_string':0xd157,'pop_word':0xd17a,'pop_dword':0xd186}
POINTER,BASE,LENGTH=0xe13c,0x9062,0x3aca
ERROR,COPY,COPY_END=0x4efb,0x85b4,0x85fc

ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_stack_reserve,aspect_stack_push_word,aspect_stack_push_dword
extern aspect_stack_push_eight,aspect_stack_push_string,aspect_stack_pop_word,aspect_stack_pop_dword
global _run_stack
_run_stack:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov word [_aborted],0
 mov [saved_sp],sp
 mov si,0x1111
 mov di,0x2222
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 mov [_result_low],ax
 mov [_result_high],dx
 cmp sp,[saved_sp]
 jne run_bad
 cmp si,0x1111
 jne run_bad
 cmp di,0x2222
 je run_done
run_bad:
 inc word [_abi_bad]
 jmp short run_done
run_aborted:
 mov word [_aborted],1
 mov sp,[saved_sp]
run_done:
 pop es
 pop di
 pop si
 pop bp
 ret
operations: dw reserve,push_word,push_dword,push_eight,push_string,pop_word,pop_dword
reserve:
 push word [bp+6]
 call aspect_stack_reserve
 ret
push_word:
 push word [bp+6]
 call aspect_stack_push_word
 ret
push_dword:
 push word [bp+8]
 push word [bp+6]
 call aspect_stack_push_dword
 ret
push_eight:
 push word [bp+6]
 call aspect_stack_push_eight
 ret
push_string:
 push word [bp+6]
 call aspect_stack_push_string
 ret
pop_word:
 call aspect_stack_pop_word
 ret
pop_dword:
 call aspect_stack_pop_dword
 ret
global aspect_stack_error
aspect_stack_error:
 push bp
 mov bp,sp
 inc word [_errors]
 cmp word [bp+4],105
 je .argok
 inc word [_abi_bad]
.argok:
 cmp word [_error_returns],0
 je run_aborted
 pop bp
 ret 2
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_stack_pointer,aspect_stack_arena,_pointer,_arena,_arena_storage
 global _errors,_abi_bad,_aborted,_error_returns,_result_low,_result_high
aspect_stack_pointer:
_pointer: dw 0
_errors: dw 0
_abi_bad: dw 0
_aborted: dw 0
_error_returns: dw 0
_result_low: dw 0
_result_high: dw 0
saved_sp: dw 0
_arena_storage: times 4 db 0
aspect_stack_arena:
_arena: times 0x3aca+128 db 0
'''

C=r'''
#include <stdio.h>
#include <string.h>
extern unsigned pointer,errors,abi_bad,aborted,error_returns,result_low,result_high;
extern unsigned char arena_storage[4+0x3aca+128];
#define arena (arena_storage+4)
extern void run_stack(unsigned op,unsigned low,unsigned high);
static unsigned char payload[256],expected[128];
static unsigned long checks;static unsigned failures;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL %lu\n",checks);}}
static void reset(void){
 memset(arena,0xa5,0x3aca+128);pointer=(unsigned)arena;
 errors=abi_bad=aborted=error_returns=0;
}
static void call(unsigned op,unsigned low,unsigned high){run_stack(op,low,high);ck(!abi_bad);}
int main(void){unsigned i,j,size,limit=(unsigned)arena+0x3aca;unsigned long value;FILE *f;
 reset();
 for(i=0;i<256;++i){call(1,i*257,0);ck(pointer==(unsigned)arena+(i+1)*2);}
 for(i=256;i>0;--i){call(5,0,0);ck(result_low==(i-1)*257);}
 ck(pointer==(unsigned)arena && !errors);
 for(i=0;i<256;++i){value=(unsigned long)i*0x01010101UL;call(2,(unsigned)value,(unsigned)(value>>16));}
 for(i=256;i>0;--i){value=(unsigned long)(i-1)*0x01010101UL;call(6,0,0);ck(result_low==(unsigned)value && result_high==(unsigned)(value>>16));}
 ck(pointer==(unsigned)arena && !errors);
 for(i=0;i<256;++i)payload[i]=(unsigned char)(i*73+19);
 for(j=0;j<2;++j){
  size=j?81:8;
  for(i=0;i<16;++i){
   reset();pointer=(unsigned)arena+i;call(j?4:3,(unsigned)(payload+i),0);
   ck(pointer==(unsigned)arena+i+size);ck(!memcmp(arena+i,payload+i,size));
   ck(arena[i+size]==0xa5);if(i)ck(arena[i-1]==0xa5);ck(!errors);
  }
  /* Actual native85B4 executes both overlapping-copy directions. */
  reset();memcpy(arena,payload,128);memcpy(expected,payload,128);
  memmove(expected+1,expected,size);pointer=(unsigned)arena+1;call(j?4:3,(unsigned)arena,0);
  ck(!memcmp(arena,expected,128));ck(!errors);
  reset();memcpy(arena,payload,128);memcpy(expected,payload,128);
  memmove(expected,expected+1,size);call(j?4:3,(unsigned)arena+1,0);
  ck(!memcmp(arena,expected,128));ck(!errors);
 }
 for(i=0;i<=128;++i){reset();pointer=limit-i;call(0,i,0);ck(!errors && pointer==limit-i);}
 for(i=0;i<4;++i){
  size=i==0?2:i==1?4:i==2?8:81;
  reset();pointer=limit-size;call(i+1,i<2?0x1234:(unsigned)payload,0xabcd);
  ck(!errors && pointer==limit);
  reset();pointer=limit-size+1;call(i+1,i<2?0x1234:(unsigned)payload,0xabcd);
  ck(errors==1 && aborted && pointer==limit-size+1);
  ck(arena[0x3aca-size+1]==0xa5);
  reset();error_returns=1;pointer=limit-size+1;
  call(i+1,i<2?0x1234:(unsigned)payload,0xabcd);
  ck(errors==1 && !aborted && pointer==limit+1);
  /* Dedicated fixturepadding permits observing preserved out-of-bounds writes. */
 }
 /* Unchecked underflow observed inside the fixture's allocated prefix. */
 reset();*((unsigned *)(arena-2))=0x7621;call(5,0,0);
 ck(!errors && pointer==(unsigned)arena-2 && result_low==0x7621);
 reset();*((unsigned *)(arena-4))=0x1234;*((unsigned *)(arena-2))=0x5678;
 call(6,0,0);ck(!errors && pointer==(unsigned)arena-4 && result_low==0x1234 && result_high==0x5678);
 f=fopen("DONE.TXT","w");if(!f)return 2;
 fprintf(f,"ASPECT_STACK %lu checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_STACK %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'src/aspect/value_stack.asm';move=ROOT/'reconstruction/erase/move_bytes.asm'
    inc='-I'+str(ROOT/'reconstruction/uart')+'/'
    for fmt,defs,target in [('bin',['-DASPECT_STACK_FLAT'],'stack.bin'),('obj',[],'stack.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(source),'-o',str(OUT/target)],check=True)
    assert len((OUT/'stack.bin').read_bytes())==END-START
    for fmt,defs,target in [('bin',[],'copy.bin'),('obj',['-DERASE_OMF'],'copy.obj')]:
        subprocess.run(['nasm','-f',fmt,*defs,inc,str(move),'-o',str(OUT/target)],check=True)
    (OUT/'callbacks.asm').write_text(ASM);(OUT/'diagnostic.c').write_text(C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
                    '-fm=STACK.map','-fe=STACK.EXE',str(OUT/'diagnostic.c'),str(OUT/'stack.obj'),
                    str(OUT/'copy.obj'),str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    inputs=[source,move,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
    report=dict(binary_sha256=sha((OUT/'STACK.EXE').read_bytes()),flat_sha256=sha((OUT/'stack.bin').read_bytes()),
                copy_sha256=sha((OUT/'copy.bin').read_bytes()),original_inputs=[],
                sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},
                scope='Exact typed stack primitives and native memory copy; diagnostic error callbacks only. Native unchecked pop/wrap and error-return behavior retained; no safe production stack or VM claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
