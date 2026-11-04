BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern display_geometry,display_detect,display_select_rows,display_baseline
global _display_rows_geometry,_display_rows_detect,_display_rows_select,_display_rows_baseline
global _display_rows_supported
%macro begin 1
%1:
 push bp
 mov bp,sp
 push si
 push di
 push es
%endmacro
%macro finish 0
 pop es
 pop di
 pop si
 pop bp
 ret
%endmacro
begin _display_rows_geometry
 call display_geometry
 finish
begin _display_rows_detect
 call display_detect
 finish
begin _display_rows_select
 push word [bp+4]
 call display_select_rows
 finish
begin _display_rows_baseline
 call display_baseline
 finish
begin _display_rows_supported
 mov ah,0x0f
 int 0x10
 cmp ah,80
 jne .bad
 or bh,bh
 jnz .bad
 cmp al,2
 je .ok
 cmp al,3
 je .ok
 cmp al,7
 jne .bad
.ok:
 xor ax,ax
 jmp short .done
.bad:
 mov ax,2
.done:
 finish

SEGMENT _DATA public class=DATA use16
; Preserve native relative overlap, including byte7A85 within viewport WORD.
display_state: times 46 db 0
%macro field 3
 global %1,%2
 %1 equ display_state+%3-0x7a66
 %2 equ %1
%endmacro
field display_legacy,_display_rows_legacy,0x7a66
field display_extended_mode,_display_rows_extended_mode,0x7a68
field display_font_capable,_display_rows_font_capable,0x7a6e
field display_scanline_capable,_display_rows_scanline_capable,0x7a70
field display_columns,_display_rows_columns,0x7a72
field display_rows,_display_rows_rows,0x7a74
field display_mode,_display_rows_mode,0x7a76
field display_segment,_display_rows_segment,0x7a78
field display_stride,_display_rows_stride,0x7a7a
field display_bytes,_display_rows_bytes,0x7a7c
field display_last_column,_display_rows_last_column,0x7a7e
field display_last_row,_display_rows_last_row,0x7a80
field display_last_line,_display_rows_last_line,0x7a82
field display_viewport,_display_rows_viewport,0x7a84
field display_cursor_row,_display_rows_cursor_row,0x7a85
field display_mono,_display_rows_mono,0x7a86
field display_cursor_start,_display_rows_cursor_start,0x7a88
field display_cursor_end,_display_rows_cursor_end,0x7a8a
field display_cells,_display_rows_cells,0x7a8c
field display_status_port,_display_rows_status_port,0x7a8e
field display_crt,_display_rows_crt,0x7a90
field display_snow,_display_rows_snow,0x7a92
