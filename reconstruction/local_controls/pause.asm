; Original overlay 3 Screen Pause entry DD7E..DDC7 (74 bytes).
; DS=SS; the native save/restore services clean three word arguments.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0xdd7e
%define pause_send_abu 0xab0b
%define pause_hide_cursor 0x6e5a
%define pause_save_cells 0x765c
%define pause_center_text 0x3226
%define pause_read_key 0x64fe
%define pause_restore_cells 0x7682
%define pause_show_cursor 0x6dca
%define pause_cell_count 0x7a72
%define pause_cell_start 0x7a82
%define pause_message 0x2eb4
%else
SEGMENT PAUSE_NATIVE_CODE public align=16 class=FARCODE use16
extern pause_send_abu,pause_hide_cursor,pause_save_cells,pause_center_text
extern pause_read_key,pause_restore_cells,pause_show_cursor
extern pause_cell_count,pause_cell_start,pause_message
global local_pause_dd7e
%endif
local_pause_dd7e:
 push bp
 db 0x8b,0xec ; MOV BP,SP, original direction-bit encoding.
 sub sp,0x108
 mov ax,0x13
 push ax
 call pause_send_abu
 call pause_hide_cursor
 lea ax,[bp-0x108]
 push ax
 push word [pause_cell_start]
 push word [pause_cell_count]
 call pause_save_cells
 push word [pause_message]
 call pause_center_text
 pop bx
 call pause_read_key
 lea ax,[bp-0x108]
 push ax
 push word [pause_cell_start]
 push word [pause_cell_count]
 call pause_restore_cells
 call pause_show_cursor
 mov ax,0x11
 push ax
 call pause_send_abu
 db 0x8b,0xe5 ; MOV SP,BP, original direction-bit encoding.
 pop bp
 ret
