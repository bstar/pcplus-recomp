; Exact resident798E..79A8 cursor reader,26 bytes; no new cursor state.
; NearRET AX=packed row/column. BDA leg ES=0040; BIOS leg INT10/AH03,BH0.
; BX/CX/DX/ES/FLAGS may be clobbered; SI/DI/BP and stack preserved.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_BREAK_CURSOR_FLAT
ORG 0x798e
%define screen_use_bios_cursor 0x7a66
%else
SEGMENT _TEXT public class=CODE use16
global aspect_break_cursor_read
extern screen_use_bios_cursor
%endif
aspect_break_cursor_read:
 cmp word [screen_use_bios_cursor],0
 jnz .bios
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 ret
.bios:
 xor_load bh,bh
 mov ah,3
 int 0x10
 mov_load ax,dx
 ret
