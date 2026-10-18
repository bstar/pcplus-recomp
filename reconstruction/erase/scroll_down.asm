; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_scroll_down
%define short
%else
ORG 0x6ec2
%endif
%include "encodings.inc"
erase_scroll_down:
L_6ec2: mov_load bx,sp
L_6ec4: mov ax,[bx+0x8]
L_6ec7: mov cx,[bx+0x6]
L_6eca: mov dx,[bx+0x4]
L_6ecd: mov bx,[bx+0x2]
L_6ed0: mov_load bh,bl
L_6ed2: mov ah,0x7
L_6ed4: push bp
L_6ed5: int byte 0x10
L_6ed7: pop bp
L_6ed8: ret word 0x8
