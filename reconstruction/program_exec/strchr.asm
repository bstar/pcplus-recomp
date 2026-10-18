; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strchr
%define short
%else
ORG 0x8c2a
%endif
%include "encodings.inc"
program_strchr:
L_8c2a: push bp
L_8c2b: mov_load bp,sp
L_8c2d: push di
L_8c2e: mov di,[bp+0x4]
L_8c31: push ds
L_8c32: pop es
L_8c33: mov_load bx,di
L_8c35: xor_load ax,ax
L_8c37: mov cx,0xffff
L_8c3a: repne scasb
L_8c3c: inc cx
L_8c3d: neg cx
L_8c3f: mov al,[bp+0x6]
L_8c42: mov_load di,bx
L_8c44: repne scasb
L_8c46: dec di
L_8c47: cmp [di],al
L_8c49: jz short L_8c4d
L_8c4b: xor_load di,di
L_8c4d: mov_load ax,di
L_8c4f: pop di
L_8c50: mov_load sp,bp
L_8c52: pop bp
L_8c53: ret
