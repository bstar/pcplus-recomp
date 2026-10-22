; Native yes/no policy on the ordinary child DS=SS VM stack. The maintained
; UI adapters own a cooperative parent frame instead of a blocking BIOS menu.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_abort_yesno
extern _runtime_abort_write,_runtime_abort_position
global _runtime_abort_confirm_native,abort_choice_write,abort_cursor_set
global _runtime_abort_bell
_runtime_abort_confirm_native:
 mov ax,0x031a
 push ax
 mov ax,0x1f
 push ax
 xor ax,ax
 push ax
 call aspect_abort_yesno
 ret
abort_choice_write:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _runtime_abort_write
 add sp,6
 pop bp
 ret 6
abort_cursor_set:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_abort_position
 add sp,2
 pop bp
 ret 2
_runtime_abort_bell:
 push bp
 push bx
 mov ax,0x0e07
 xor bx,bx
 int 0x10
 pop bx
 pop bp
 ret
