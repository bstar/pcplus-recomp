; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_far_fill
%define short
%else
ORG 0x63fa
%endif
%include "encodings.inc"
erase_far_fill:
L_63fa: mov_load bx,sp
L_63fc: mov cx,[bx+0x2]
L_63ff: jcxz L_640f
L_6401: mov_load dx,di
L_6403: les di,word [bx+0x6]
L_6406: mov ax,[bx+0x4]
L_6409: xchg ah,al
L_640b: rep stosw
L_640d: mov_load di,dx
L_640f: ret word 0x8
