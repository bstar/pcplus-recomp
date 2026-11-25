; Recovered PCPlus 2.01 VT52 direct cursor address (ESC Y row col, 1f70..1fa0).
; The flat build is checked against the original by recover.py (analyst only).
BITS 16
CPU 8086
%ifdef VT52_OMF
SEGMENT VT52_CODE public align=16 class=FARCODE use16
global vt52_cursor_address
extern vt52f_next_byte,vt52f_set_cursor,csi_last_row,screen_last_column
%define ansi_next_byte vt52f_next_byte
%define screen_set_cursor vt52f_set_cursor
%define short
%else
ORG 0x1f70
%define ansi_next_byte 0x5ca0
%define screen_set_cursor 0x1bbe
%define csi_last_row 0x334a
%define screen_last_column 0x3258
%endif
%include "encodings.inc"
vt52_cursor_address:
L_1f70: push di
L_1f71: push si
L_1f72: call ansi_next_byte
L_1f75: mov_load di,ax
L_1f77: sub di,strict byte 0x20
L_1f7a: call ansi_next_byte
L_1f7d: mov_load si,ax
L_1f7f: sub si,strict byte 0x20
; Unsigned clamps: a parameter below 20h wraps high and clamps to the last row/column.
L_1f82: cmp [csi_last_row],di
L_1f86: jnc short L_1f8c
L_1f88: mov di,[csi_last_row]
L_1f8c: cmp [screen_last_column],si
L_1f90: jnc short L_1f96
L_1f92: mov si,[screen_last_column]
L_1f96: mov_load ax,di
L_1f98: mov_load dx,si
L_1f9a: call screen_set_cursor
L_1f9d: pop si
L_1f9e: pop di
L_1f9f: ret
