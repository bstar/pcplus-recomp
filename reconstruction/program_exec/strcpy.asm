; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strcpy
%define short
%else
ORG 0x8268
%endif
%include "encodings.inc"
program_strcpy:
L_8268: push bp
L_8269: mov_load bp,sp
L_826b: mov_load dx,di
L_826d: mov_load bx,si
L_826f: mov si,[bp+0x6]
L_8272: mov_load di,si
L_8274: mov ax,ds
L_8276: mov es,ax
L_8278: xor_load ax,ax
L_827a: mov cx,0xffff
L_827d: repne scasb
L_827f: not cx
L_8281: mov di,[bp+0x4]
L_8284: mov_load ax,di
L_8286: test al,0x1
L_8288: jz short L_828c
L_828a: movsb
L_828b: dec cx
L_828c: shr cx,1
L_828e: rep movsw
L_8290: adc_load cx,cx
L_8292: rep movsb
L_8294: mov_load si,bx
L_8296: mov_load di,dx
L_8298: pop bp
L_8299: ret
