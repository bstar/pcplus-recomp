; Real INT33 storage API and native callee-cleanup adapters, near cdecl.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern mouse_init,mouse_probe,mouse_depth
%ifdef MOUSE_BANK
extern mouse_keyboard_poll_resident,mouse_keyboard_read_resident
%else
extern keyboard_poll,keyboard_read
%endif
global _mouse_platform_size,_mouse_platform_save,_mouse_platform_restore
global _mouse_platform_init,_mouse_platform_reset,_mouse_platform_depth
global _mouse_platform_poll,_mouse_platform_read
_mouse_platform_size:
 push bx
 xor bx,bx
 mov ax,0x15
 int 0x33
 mov ax,bx
 pop bx
 ret
_mouse_platform_save:
 mov ax,0x16
 jmp state_io
_mouse_platform_restore:
 mov ax,0x17
state_io:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov dx,[bp+4]
 mov es,[bp+6]
 int 0x33
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_mouse_platform_init:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,1
 push ax
 push word [bp+4] ; x
 push word [bp+6] ; y; native near stack order is y,x,reset
 call mouse_init
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_mouse_platform_reset:
 push bx
 push si
 push di
 push es
 mov ax,1
 push ax
 call mouse_probe
 pop es
 pop di
 pop si
 pop bx
 ret
_mouse_platform_depth:
 mov ax,[cs:mouse_depth]
 ret
_mouse_platform_poll:
 push bx
 push si
 push di
 push es
%ifdef MOUSE_BANK
 call far mouse_keyboard_poll_resident
%else
 call keyboard_poll
%endif
 jmp key_return
_mouse_platform_read:
 push bx
 push si
 push di
 push es
%ifdef MOUSE_BANK
 call far mouse_keyboard_read_resident
%else
 call keyboard_read
%endif
key_return:
 pop es
 pop di
 pop si
 pop bx
 ret
