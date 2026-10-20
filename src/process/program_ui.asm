; Maintained cdecl adapters for recovered PROGRAM screen services.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern display_cursor,display_cursor_shape,display_clear,display_set_mode
extern display_scanlines,display_wait
extern _native_program_wait_key
global display_wait_key
display_wait_key:
%ifdef NATIVE_PROGRAM_FAR
 call far _native_program_wait_key
 ret
%else
 jmp _native_program_wait_key
%endif
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cld
%endmacro
%macro leave 0
 cld
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
%endmacro
%macro unary 2
global %1
%1:
 enter
 push word [bp+4]
 call %2
 leave
%endmacro
unary _program_ui_cursor,display_cursor
unary _program_ui_clear,display_clear
unary _program_ui_mode,display_set_mode
global _program_ui_shape,_program_ui_scanlines,_program_ui_wait
global _program_ui_key_available
_program_ui_key_available:
 enter
 mov ah,1
 int 0x16
 pushf
 pop ax
 xor ax,0x40
 and ax,0x40
 leave
_program_ui_shape:
 enter
 xor bx,bx
 call display_cursor_shape
 leave
_program_ui_scanlines:
 enter
 mov bx,[bp+4]
 call display_scanlines
 leave
_program_ui_wait:
 enter
 call display_wait
 leave
SEGMENT _DATA public class=DATA use16
global display_wait_message,_program_ui_wait_message
display_wait_message:
_program_ui_wait_message: dw 0
