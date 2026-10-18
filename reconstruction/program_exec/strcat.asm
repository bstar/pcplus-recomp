; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strcat
%define short
%else
ORG 0x8bea
%endif
%include "encodings.inc"
program_strcat:
L_8bea: push bp
L_8beb: mov_load bp,sp
L_8bed: mov_load dx,di
L_8bef: mov_load bx,si
L_8bf1: mov ax,ds
L_8bf3: mov es,ax
L_8bf5: mov di,[bp+0x4]
L_8bf8: xor_load ax,ax
L_8bfa: mov cx,0xffff
L_8bfd: repne scasb
L_8bff: lea si,[di-0x1]
L_8c02: mov di,[bp+0x6]
L_8c05: mov cx,0xffff
L_8c08: repne scasb
L_8c0a: not cx
L_8c0c: sub_load di,cx
L_8c0e: xchg di,si
L_8c10: mov ax,[bp+0x4]
L_8c13: test si,0x1
L_8c17: jz short L_8c1b
L_8c19: movsb
L_8c1a: dec cx
L_8c1b: shr cx,1
L_8c1d: rep movsw
L_8c1f: adc_load cx,cx
L_8c21: rep movsb
L_8c23: mov_load si,bx
L_8c25: mov_load di,dx
L_8c27: pop bp
L_8c28: ret
