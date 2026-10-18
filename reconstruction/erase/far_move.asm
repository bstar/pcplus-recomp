; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_far_move
%define short
%else
ORG 0x6412
%endif
%include "encodings.inc"
erase_far_move:
L_6412: mov_load bx,sp
L_6414: mov cx,[bx+0x2]
L_6417: jcxz L_6448
L_6419: push ds
L_641a: push di
L_641b: push si
L_641c: les di,word [bx+0x8]
L_641f: lds si,word [bx+0x4]
L_6422: mov ax,es
L_6424: mov dx,ds
L_6426: cmp_load ax,dx
L_6428: jnz short L_6442
L_642a: cmp_load di,si
L_642c: jna short L_6442
L_642e: mov_load ax,cx
L_6430: shl ax,1
L_6432: add_load ax,si
L_6434: cmp_load di,ax
L_6436: jnc short L_6442
L_6438: mov_load ax,cx
L_643a: dec ax
L_643b: shl ax,1
L_643d: add_load si,ax
L_643f: add_load di,ax
L_6441: std
L_6442: rep movsw
L_6444: cld
L_6445: pop si
L_6446: pop di
L_6447: pop ds
L_6448: ret word 0xa
