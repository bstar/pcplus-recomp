; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_strcmpi
%define short
%else
ORG 0x93de
%endif
%include "encodings.inc"
program_strcmpi:
L_93de: push bp
L_93df: mov_load bp,sp
L_93e1: mov_load dx,si
L_93e3: mov si,[bp+0x6]
L_93e6: mov bx,[bp+0x4]
L_93e9: mov al,0xff
L_93eb: or_load al,al
L_93ed: jz short L_941b
L_93ef: lodsb
L_93f0: mov ah,[bx]
L_93f2: inc bx
L_93f3: cmp_load ah,al
L_93f5: jz short L_93eb
L_93f7: sub al,0x41
L_93f9: cmp al,0x1a
L_93fb: sbb_load cl,cl
L_93fd: and cl,0x20
L_9400: add_load al,cl
L_9402: add al,0x41
L_9404: xchg ah,al
L_9406: sub al,0x41
L_9408: cmp al,0x1a
L_940a: sbb_load cl,cl
L_940c: and cl,0x20
L_940f: add_load al,cl
L_9411: add al,0x41
L_9413: cmp_load al,ah
L_9415: jz short L_93eb
L_9417: sbb_load al,al
L_9419: sbb al,0xff
L_941b: cbw
L_941c: mov_load si,dx
L_941e: pop bp
L_941f: ret
