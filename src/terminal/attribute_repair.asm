; Keep the resident RET2 ABI while exact repair executes in ASPECT_CODE.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_abort,erase_default_attribute,erase_previous_attribute,text_write_char
global erase_repair_attributes,repair_abort_far
erase_repair_attributes:
 push bp
 mov bp,sp
 push word [bp+4]
 call far attribute_repair_checked_far
 pop bp
 ret 2
repair_abort_far:
 mov ax,0x2d98
 jmp terminal_abort
repair_default_far:
 call erase_default_attribute
 retf
repair_previous_far:
 push bp
 mov bp,sp
 push word [bp+6]
 call erase_previous_attribute
 pop bp
 retf 2
repair_text_far:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 call text_write_char
 pop bp
 retf 4

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attribute_repair_native,attribute_geometry_admit,attribute_plane_admit
extern screen_cursor_wrap,erase_attribute_values_base,erase_attribute_values
global attribute_repair_checked_far,attribute_repair_admit,attribute_repair_admit_far
global repair_default_attribute,repair_previous_attribute,repair_text_write_char
; Read-only fixed-plane admission. Native wrap-disabled repair is a no-op.
attribute_repair_admit:
 cmp word [screen_cursor_wrap],0
 je .okay
 call attribute_geometry_admit
 jc .bad
 jmp .values
.plane:
 call attribute_plane_admit
 jc .bad
.values:
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .bad
.okay:
 clc
 ret
.bad:
 stc
 ret
attribute_repair_checked_far:
 push bp
 mov bp,sp
 cmp word [screen_cursor_wrap],0
 je .native
 cmp word [bp+6],0
 je .plane
 call attribute_repair_admit
 jmp .checked
.plane:
 call attribute_repair_admit.plane
.checked:
 jc .invalid
.native:
 push word [bp+6]
 call attribute_repair_native
 pop bp
 retf 2
.invalid:
 call far repair_abort_far
 ; The resident abort unwinds the application. This cannot return normally.
global attribute_repair_plane_admit
attribute_repair_plane_admit equ attribute_repair_admit.plane
attribute_repair_admit_far:
 push bx
 push cx
 push dx
 push si
 push di
 call attribute_repair_admit
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 retf
repair_default_attribute:
 call far repair_default_far
 ret
repair_previous_attribute:
 push bp
 mov bp,sp
 push word [bp+4]
 call far repair_previous_far
 pop bp
 ret 2
repair_text_write_char:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call far repair_text_far
 pop bp
 ret 4
