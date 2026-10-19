#!/usr/bin/env python3
"""Build exact global-string lifecycle and source-owned8086 DOS diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/aspect-globals'
START, RELEASE, END = 0xd850, 0xd88e, 0xd8b5
SOURCE_FILE_START = 60000
SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
HOOKS = {'read':0x4cb4,'alloc':0x860f,'error':0x4efb,'free':0x85fc}
COUNT, TABLE = 0xe3be, 0xdb82

ASM = r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_globals_initialize,aspect_globals_release
extern _pool,_failure_at,_error_returns
global _run_globals,_release_globals
_run_globals:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,[bp+4]
 mov [read_value],ax
 mov ax,ds
 mov [_data_segment],ax
 mov word [_aborted],0
 mov [saved_sp],sp
 mov si,0x1111
 mov di,0x2222
 call aspect_globals_initialize
 cmp si,0x1111
 jne run_bad
 cmp di,0x2222
 je run_done
run_bad:
 inc word [_calls+8]
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
_release_globals:
 push si
 push di
 push es
 mov si,0x3333
 mov di,0x4444
 call aspect_globals_release
 cmp si,0x3333
 jne .bad
 cmp di,0x4444
 je .done
.bad:
 inc word [_calls+8]
.done:
 pop es
 pop di
 pop si
 ret
global aspect_globals_read,aspect_globals_alloc,aspect_globals_error,aspect_globals_free
aspect_globals_read:
 inc word [_calls]
 mov ax,[read_value]
 ret
aspect_globals_alloc:
 push bp
 mov bp,sp
 cmp word [bp+4],81
 je .ok
 inc word [_calls+8]
.ok:
 mov ax,[_calls+2]
 inc word [_calls+2]
 cmp ax,[_failure_at]
 je .failed
 mov cx,81
 mul cx
 add ax,_pool
 mov dx,ds
 pop bp
 ret
.failed:
 xor ax,ax
 xor dx,dx
 pop bp
 ret
aspect_globals_error:
 push bp
 mov bp,sp
 inc word [_calls+4]
 cmp word [bp+4],101
 je .ok
 inc word [_calls+8]
.ok:
 cmp word [_error_returns],0
 je run_aborted
 pop bp
 ret 2
aspect_globals_free:
 push bp
 mov bp,sp
 mov bx,[_calls+6]
 inc word [_calls+6]
 shl bx,1
 shl bx,1
 mov ax,[bp+4]
 mov [_freed+bx],ax
 mov ax,[bp+6]
 mov [_freed+bx+2],ax
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_globals_count,aspect_globals_table,_global_count,_global_table
global _calls,_freed,_aborted,_data_segment
aspect_globals_count:
_global_count: dw 0
aspect_globals_table:
_global_table: times 130 dd 0
_calls: times 5 dw 0
_freed: times 128 dd 0
_aborted: dw 0
_data_segment: dw 0
saved_sp: dw 0
read_value: dw 0
'''

C = r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
extern unsigned global_count,calls[5],aborted,data_segment;
extern unsigned long global_table[130],freed[128];
extern void run_globals(unsigned count);
extern void release_globals(void);
unsigned char pool[128][81];
unsigned failure_at,error_returns;
static unsigned long checks;static unsigned failures;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL %lu\n",checks);}}
static void setup(void){
 memset(global_table,0xcc,sizeof(global_table));memset(pool,0xa5,sizeof(pool));
 memset(calls,0,sizeof(calls));memset(freed,0,sizeof(freed));
 failure_at=0xffff;error_returns=0;
}
static unsigned long ptr(unsigned i){return ((unsigned long)data_segment<<16)+(unsigned)&pool[i][0];}
static void verify(unsigned n,unsigned failed,unsigned aborting){
 unsigned i,j,attempts=aborting?failed+1:n;
 ck(global_count==n);ck(calls[0]==1);ck(calls[1]==attempts);
 ck(calls[2]==(failed!=0xffff));ck(calls[3]==0);ck(calls[4]==0);ck(aborted==aborting);
 for(i=0;i<attempts;++i){
  ck(global_table[i]==(i==failed?0UL:ptr(i)));
  ck(pool[i][0]==(i==failed?0xa5:0));
  for(j=1;j<81;++j)ck(pool[i][j]==0xa5);
 }
 for(i=attempts;i<130;++i)ck(global_table[i]==0xccccccccUL);
}
int main(void){unsigned n,i,f;FILE *out;
 for(n=0;n<=128;++n){
  setup();run_globals(n);verify(n,0xffff,0);release_globals();
  ck(calls[3]==n);ck(global_count==n);ck(calls[4]==0);
  for(i=0;i<n;++i){ck(freed[i]==ptr(i));ck(global_table[i]==ptr(i));}
 }
 /* Returning error callback is a deliberate model, not real101 recovery. */
 for(f=0;f<3;++f){
  setup();failure_at=f;error_returns=1;run_globals(3);verify(3,f,0);
  release_globals();ck(calls[3]==2);ck(global_count==3);
  for(i=0,n=0;i<3;++i)if(i!=f){ck(freed[n++]==ptr(i));ck(global_table[i]==ptr(i));}
 }
 /* Abort callback models only nonlocal control transfer, no rollback. */
 for(f=0;f<3;++f){
  setup();failure_at=f;run_globals(3);verify(3,f,1);
  /* Do not release uninitialized tail; diagnostic asserts exact partial state. */
  ck(calls[3]==0);ck(global_count==3);
 }
 out=fopen("DONE.TXT","w");if(!out)return 2;
 fprintf(out,"ASPECT_GLOBALS %lu checks %u failures\n",checks,failures);fclose(out);
 printf("ASPECT_GLOBALS %lu checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'src/aspect/global_strings.asm'
    inc='-I'+str(ROOT/'reconstruction/uart')+'/'
    subprocess.run(['nasm','-f','bin','-DASPECT_GLOBALS_FLAT',inc,str(source),
                    '-o',str(OUT/'globals.bin'),'-l',str(OUT/'globals-flat.lst')],check=True)
    assert len((OUT/'globals.bin').read_bytes())==END-START
    subprocess.run(['nasm','-f','obj',inc,str(source),'-o',str(OUT/'globals.obj')],check=True)
    (OUT/'callbacks.asm').write_text(ASM);(OUT/'diagnostic.c').write_text(C)
    subprocess.run(['nasm','-f','obj',str(OUT/'callbacks.asm'),'-o',str(OUT/'callbacks.obj')],check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
                    '-fm=GLOBALS.map','-fe=GLOBALS.EXE',str(OUT/'diagnostic.c'),str(OUT/'globals.obj'),
                    str(OUT/'callbacks.obj')],cwd=OUT,check=True)
    inputs=[source,ROOT/'reconstruction/uart/encodings.inc',Path(__file__).resolve()]
    report=dict(binary_sha256=sha((OUT/'GLOBALS.EXE').read_bytes()),flat_sha256=sha((OUT/'globals.bin').read_bytes()),
                sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in inputs},original_inputs=[],
                scope='Recovered lifecycle only; source-owned farheap/error callbacks. Counts0..128; no heap manager, full loader, or ASPECT VM claim.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
