BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern display_geometry,display_snapshot,display_restore
extern _display_platform_allocate,_display_platform_free
global _display_probe_native,_display_snapshot_native,_display_restore_native
global display_allocate,display_free
display_allocate: jmp _display_platform_allocate
display_free: jmp _display_platform_free
_display_probe_native:
 push es
 call display_geometry
 pop es
 ret
_display_snapshot_native:
 push es
 cld
 call display_snapshot
 pop es
 ret
_display_restore_native:
 push bp
 mov bp,sp
 push es
 push word [bp+6]
 push word [bp+4]
 cld
 call display_restore ;Native callee pops its four argument bytes.
 pop es
 pop bp
 ret ;The C caller owns its separate original argument bytes.
SEGMENT _DATA public class=DATA use16
; Preserve native relative overlap, including cursor-row byte at7a85.
display_state: times 46 db 0
%macro field 3
 global %1,%2
 %1 equ display_state+%3-0x7a66
 %2 equ %1
%endmacro
field display_legacy,_native_display_legacy,0x7a66
field display_extended_mode,_native_display_extended_mode,0x7a68
field display_cursor_policy,_native_display_cursor_policy,0x7a6c
field display_columns,_native_display_columns,0x7a72
field display_rows,_native_display_rows,0x7a74
field display_mode,_native_display_mode,0x7a76
field display_segment,_native_display_segment,0x7a78
field display_stride,_native_display_stride,0x7a7a
field display_bytes,_native_display_bytes,0x7a7c
field display_last_column,_native_display_last_column,0x7a7e
field display_last_row,_native_display_last_row,0x7a80
field display_last_line,_native_display_last_line,0x7a82
field display_viewport,_native_display_viewport,0x7a84
field display_cursor_row,_native_display_cursor_row,0x7a85
field display_mono,_native_display_mono,0x7a86
field display_cursor_start,_native_display_cursor_start,0x7a88
field display_cursor_end,_native_display_cursor_end,0x7a8a
field display_cells,_native_display_cells,0x7a8c
field display_status_port,_native_display_status_port,0x7a8e
field display_crt,_native_display_crt,0x7a90
field display_snow,_native_display_snow,0x7a92
