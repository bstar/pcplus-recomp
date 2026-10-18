; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_read_packed
extern ui_read_byte
%define short
%else
ORG 0x6fd0
%define ui_read_byte 0x6fa0
%endif
%include "encodings.inc"
ui_read_packed:
L_6fd0: mov_load bx,sp
L_6fd2: push di
L_6fd3: mov di,[bx+0x2]
L_6fd6: push di
L_6fd7: call ui_read_byte
L_6fda: inc di
L_6fdb: push di
L_6fdc: mov_load di,ax
L_6fde: call ui_read_byte
L_6fe1: xchg al,ah
L_6fe3: or_load ax,di
L_6fe5: xchg al,ah
L_6fe7: pop di
L_6fe8: ret word 0x2
