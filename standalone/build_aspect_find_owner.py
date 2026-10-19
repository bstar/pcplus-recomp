#!/usr/bin/env python3
"""Link real DOS near heap with the maintained FIND temporary owner."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-find-owner'
ASM=r'''
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _runtime_find_reset,_runtime_find_alloc,_runtime_find_free,_runtime_find_finish
extern _probe_bad,_probe_ds,_probe_ss,_probe_flags,_probe_sp_before,_probe_sp_after
global _probe
_probe:
 pushf
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [cs:saved_sp],sp
 mov [cs:saved_bp],bp
 mov ax,ds
 mov [cs:saved_ds],ax
 mov ax,ss
 mov [cs:saved_ss],ax
 mov word [cs:bad],0
 mov si,0x1234
 mov di,0x5678
 mov ax,0x4321
 mov es,ax
 cmp word [bp+10],0
 je .if0
 sti
 jmp short .ready
.if0:
 cli
.ready:
 cld
 mov ax,[bp+6]
 or ax,ax
 jz .reset
 cmp ax,1
 je .alloc
 cmp ax,2
 je .free
 call _runtime_find_finish
 xor ax,ax
 jmp short .after
.reset:
 call _runtime_find_reset
 xor ax,ax
 jmp short .after
.alloc:
 push word [bp+8]
 call _runtime_find_alloc
 add sp,2
 jmp short .after
.free:
 push word [bp+8]
 call _runtime_find_free
 add sp,2
 xor ax,ax
.after:
 mov [cs:result],ax
 pushf
 pop dx
 mov [cs:flags_after],dx
 mov ax,ds
 mov [cs:ds_after],ax
 mov ax,ss
 mov [cs:ss_after],ax
 mov [cs:sp_after],sp
 cmp sp,[cs:saved_sp]
 je .si
 or word [cs:bad],1
.si:
 cmp si,0x1234
 je .di
 or word [cs:bad],2
.di:
 cmp di,0x5678
 je .bp
 or word [cs:bad],4
.bp:
 cmp bp,[cs:saved_bp]
 je .restore
 or word [cs:bad],8
.restore:
 cli
 mov ax,[cs:saved_ss]
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov ax,[cs:saved_ds]
 mov ds,ax
 mov ax,[cs:bad]
 mov [_probe_bad],ax
 mov ax,[cs:ds_after]
 mov [_probe_ds],ax
 mov ax,[cs:ss_after]
 mov [_probe_ss],ax
 mov ax,[cs:flags_after]
 mov [_probe_flags],ax
 mov ax,[cs:saved_sp]
 mov [_probe_sp_before],ax
 mov ax,[cs:sp_after]
 mov [_probe_sp_after],ax
 mov ax,[cs:result]
 pop es
 pop di
 pop si
 pop bp
 popf
 ret
saved_sp: dw 0
saved_bp: dw 0
saved_ds: dw 0
saved_ss: dw 0
result: dw 0
flags_after: dw 0
ds_after: dw 0
ss_after: dw 0
sp_after: dw 0
bad: dw 0
'''
C=r'''
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <malloc.h>
#include "runtime.h"
#include "find_runtime.h"
unsigned runtime_error,error_calls;
unsigned probe_bad,probe_ds,probe_ss,probe_flags,probe_sp_before,probe_sp_after;
extern unsigned __cdecl probe(unsigned,unsigned,unsigned);
static unsigned long checks,failures,operations;
static unsigned char *foreign;
static unsigned long baseline;
static unsigned long int0_before;
static void ck(unsigned condition){++checks;if(!condition){++failures;if(failures<8)printf("FAIL %lu\n",checks);}}
void __cdecl runtime_set_error(unsigned value){++error_calls;if(!runtime_error)runtime_error=value;}
static void clear_error(void){runtime_error=error_calls=0;}
static unsigned call(unsigned op,unsigned argument,unsigned enabled){unsigned result;
 result=probe(op,argument,enabled);++operations;
 ck(probe_bad==0);ck(probe_ds==probe_ss);ck(probe_sp_before==probe_sp_after);
 ck((probe_flags&0x600)==(enabled?0x200:0));
 ck(*(unsigned long __far *)MK_FP(0,0)==int0_before);
 return result;
}
static unsigned long used(void){struct _heapinfo item;int status;unsigned long value=0;
 memset(&item,0,sizeof(item));
 while((status=_nheapwalk(&item))==_HEAPOK)if(item._useflag==_USEDENTRY)value+=item._size;
 ck(status==_HEAPEND);ck(_nheapchk()==_HEAPOK);return value;
}
static void foreign_ok(void){unsigned i;for(i=0;i<128;++i)ck(foreign[i]==(unsigned char)(i^0x96));}
static void put(unsigned char *p,unsigned n,unsigned seed){unsigned i;for(i=0;i<n;++i)p[i]=(unsigned char)(i+seed);}
static void intact(unsigned char *p,unsigned n,unsigned seed){unsigned i;unsigned char __far *far_view;
 far_view=(unsigned char __far *)MK_FP(probe_ds,(unsigned)p);
 for(i=0;i<n;++i){ck(p[i]==(unsigned char)(i+seed));ck(far_view[i]==p[i]);}
}
static void finish(void){clear_error();call(3,0,1);ck(runtime_error==0);ck(runtime_find_live==0);ck(used()==baseline);foreign_ok();}
static void start(void){finish();call(0,0,1);runtime_find_fail_after=65535U;clear_error();}
int main(void){unsigned n,k,enabled,live;unsigned char *a,*b,*warm;unsigned long before;FILE *out;
 int0_before=*(unsigned long __far *)MK_FP(0,0);ck(sizeof(void *)==2);
 warm=_nmalloc(4096);ck(warm!=0);if(!warm)return 2;memset(warm,0x37,4096);_nfree(warm);
 foreign=_nmalloc(128);ck(foreign!=0);if(!foreign)return 2;
 for(n=0;n<128;++n)foreign[n]=(unsigned char)(n^0x96);
 baseline=used();ck(runtime_find_live==0);ck(probe_bad==0);
 /* Every valid size, complementary independent payload, both IF states. */
 for(enabled=0;enabled<2;++enabled)for(n=1;n<=81;++n){
  start();a=(unsigned char *)call(1,n,enabled);b=(unsigned char *)call(1,82-n,enabled);
  ck(a!=0 && b!=0 && a!=b);ck(runtime_error==0);ck(runtime_find_live==2);ck(runtime_find_peak==2);
  ck((unsigned)a<=65535U-n+1U);ck((unsigned)b<=65535U-(82-n)+1U);
  put(a,n,17);put(b,82-n,93);intact(a,n,17);intact(b,82-n,93);foreign_ok();
  ck(used()>baseline);
  call(2,(unsigned)(n&1?a:b),enabled);ck(runtime_error==0);ck(runtime_find_live==1);
  if(n&1)intact(b,82-n,93);else intact(a,n,17);
  call(2,(unsigned)(n&1?b:a),enabled);ck(runtime_error==0);ck(runtime_find_live==0);ck(used()==baseline);
  finish();finish();
 }
 /* Rejected calls cannot free foreign/interior/other owned data or grow heap. */
 start();a=(unsigned char *)call(1,81,1);b=(unsigned char *)call(1,81,1);put(a,81,31);put(b,81,73);before=used();
 for(k=0;k<3;++k){clear_error();ck(call(1,k==0?0:k==1?82:65535U,k&1)==0);ck(runtime_error==ASPECT_RUN_OPERAND);ck(runtime_find_live==2);ck(used()==before);intact(a,81,31);intact(b,81,73);foreign_ok();}
 clear_error();ck(call(1,1,1)==0);ck(runtime_error==ASPECT_RUN_STATE);ck(runtime_find_live==2);ck(used()==before);
 for(k=0;k<4;++k){unsigned bad=k==0?0:k==1?65535U:k==2?(unsigned)(a+1):(unsigned)foreign;
  clear_error();call(2,bad,k&1);ck(runtime_error==ASPECT_RUN_STATE);ck(runtime_find_live==2);ck(used()==before);intact(a,81,31);intact(b,81,73);foreign_ok();
 }
 clear_error();call(2,(unsigned)a,1);ck(runtime_error==0);ck(runtime_find_live==1);before=used();
 clear_error();call(2,(unsigned)a,0);ck(runtime_error==ASPECT_RUN_STATE);ck(runtime_find_live==1);ck(used()==before);intact(b,81,73);foreign_ok();finish();
 /* Diagnostic allocation failure returns typed8, preserving partial owner. */
 for(enabled=0;enabled<2;++enabled)for(k=0;k<2;++k){
  start();runtime_find_fail_after=k;a=(unsigned char *)call(1,81,enabled);
  if(k){ck(a!=0);put(a,81,41);b=(unsigned char *)call(1,81,enabled);ck(b==0);intact(a,81,41);live=1;}
  else{ck(a==0);live=0;}
  ck(runtime_error==ASPECT_RUN_HEAP);ck(runtime_find_live==live);ck(runtime_find_peak==live);ck(runtime_find_alloc_calls==k+1);foreign_ok();
  /* Release is explicit; original native search abort is a separate proof. */
  call(3,0,enabled);ck(runtime_error==ASPECT_RUN_HEAP);ck(runtime_find_live==0);ck(used()==baseline);finish();finish();
 }
 /* Repeated partial/full cleanup and reuse catch retained/duplicate owners. */
 for(k=0;k<100;++k){start();a=(unsigned char *)call(1,81,1);ck(a!=0);put(a,81,k);if(k&1){b=(unsigned char *)call(1,1,1);ck(b!=0);put(b,1,17);}intact(a,81,k);finish();}
 foreign_ok();_nfree(foreign);ck(_nheapchk()==_HEAPOK);ck(*(unsigned long __far *)MK_FP(0,0)==int0_before);
 out=fopen("RESULT.TXT","w");if(!out)return 3;
 fprintf(out,"FIND_OWNER %lu checks %lu failures %lu operations\n",checks,failures,operations);fclose(out);
 printf("FIND_OWNER %lu checks %lu failures %lu operations\n",checks,failures,operations);return failures?1:0;
}
'''

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'owner_host.c').write_text(C);(OUT/'owner_probe.asm').write_text(ASM)
 subprocess.run(['nasm','-fobj','owner_probe.asm','-o','owner_probe.obj'],cwd=OUT,check=True)
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-dASPECT_RUNTIME_DIAGNOSTIC']
 subprocess.run(['wcc',*flags,'-fo='+str(OUT/'find_owner.obj'),'src/aspect/find_runtime.c'],cwd=ROOT,check=True)
 subprocess.run(['wcl',*flags,'-i='+str(ROOT/'src/aspect'),'-k8192','-fm=OWNER.MAP','-fe=OWNER.EXE','owner_host.c','owner_probe.obj','find_owner.obj'],cwd=OUT,check=True)
 paths=['src/aspect/find_runtime.c','src/aspect/find_runtime.h','src/aspect/runtime.h','standalone/build_aspect_find_owner.py']
 report=dict(original_inputs=[],sources={p:sha(ROOT/p) for p in paths},binary_sha256=sha(OUT/'OWNER.EXE'),
             generated={'owner_host.c':sha(OUT/'owner_host.c'),'owner_probe.asm':sha(OUT/'owner_probe.asm')},
             platform='Actual DOS smallmodel8086, near_nmalloc/_nfree, 8192stack; DS=SS,cdecl,DF0.',
             scope='Maintained near temporary owner only; typed-error-record callback, not native search or production ASM abort/unwind.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built OWNER.EXE with actual DOS nearheap and maintained FIND owner')

if __name__=='__main__':main()
