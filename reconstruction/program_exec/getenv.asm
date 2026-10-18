; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_getenv
extern program_strlen
extern program_strncmp
extern program_environ
%define short
%else
ORG 0x8e12
%define program_strlen 0x8d18
%define program_strncmp 0x9c06
%define program_environ 0x7b43
%endif
%include "encodings.inc"
program_getenv:
L_8e12: push bp
L_8e13: mov_load bp,sp
L_8e15: push di
L_8e16: push si
L_8e17: mov si,[program_environ]
L_8e1b: or_load si,si
L_8e1d: jz short L_8e63
L_8e1f: cmp word [bp+0x4],0x0
L_8e23: jz short L_8e63
L_8e25: push word [bp+0x4]
L_8e28: call program_strlen
L_8e2b: add sp,0x2
L_8e2e: mov_load di,ax
L_8e30: jmp short L_8e5e
L_8e32: push word [si]
L_8e34: call program_strlen
L_8e37: add sp,0x2
L_8e3a: cmp_load ax,di
L_8e3c: jng short L_8e5c
L_8e3e: mov bx,[si]
L_8e40: cmp byte [bx+di],0x3d
L_8e43: jnz short L_8e5c
L_8e45: push di
L_8e46: push word [bp+0x4]
L_8e49: push bx
L_8e4a: call program_strncmp
L_8e4d: add sp,0x6
L_8e50: or_load ax,ax
L_8e52: jnz short L_8e5c
L_8e54: mov ax,[si]
L_8e56: add_load ax,di
L_8e58: inc ax
L_8e59: jmp short L_8e65
L_8e5b: nop
L_8e5c: inc si
L_8e5d: inc si
L_8e5e: cmp word [si],0x0
L_8e61: jnz short L_8e32
L_8e63: sub_load ax,ax
L_8e65: pop si
L_8e66: pop di
L_8e67: mov_load sp,bp
L_8e69: pop bp
L_8e6a: ret
