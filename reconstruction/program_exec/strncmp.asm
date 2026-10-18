; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strncmp
%define short
%else
ORG 0x9c06
%endif
%include "encodings.inc"
program_strncmp:
L_9c06: push bp
L_9c07: mov_load bp,sp
L_9c09: push di
L_9c0a: push si
L_9c0b: push ds
L_9c0c: pop es
L_9c0d: mov cx,[bp+0x8]
L_9c10: jcxz L_9c38
L_9c12: mov_load bx,cx
L_9c14: mov di,[bp+0x4]
L_9c17: mov_load si,di
L_9c19: xor_load ax,ax
L_9c1b: repne scasb
L_9c1d: neg cx
L_9c1f: add_load cx,bx
L_9c21: mov_load di,si
L_9c23: mov si,[bp+0x6]
L_9c26: repe cmpsb
L_9c28: mov al,[si-0x1]
L_9c2b: xor_load cx,cx
L_9c2d: cmp al,[di-0x1]
L_9c30: ja short L_9c36
L_9c32: jz short L_9c38
L_9c34: dec cx
L_9c35: dec cx
L_9c36: not cx
L_9c38: mov_load ax,cx
L_9c3a: pop si
L_9c3b: pop di
L_9c3c: mov_load sp,bp
L_9c3e: pop bp
L_9c3f: ret
