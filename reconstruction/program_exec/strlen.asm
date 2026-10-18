; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strlen
%define short
%else
ORG 0x8d18
%endif
%include "encodings.inc"
program_strlen:
L_8d18: push bp
L_8d19: mov_load bp,sp
L_8d1b: mov_load dx,di
L_8d1d: mov ax,ds
L_8d1f: mov es,ax
L_8d21: mov di,[bp+0x4]
L_8d24: xor_load ax,ax
L_8d26: mov cx,0xffff
L_8d29: repne scasb
L_8d2b: not cx
L_8d2d: dec cx
L_8d2e: xchg ax,cx
L_8d2f: mov_load di,dx
L_8d31: pop bp
L_8d32: ret
