; Maintained runtime providers for recovered input and driver services.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_receive_character,terminal_quit,terminal_abort
extern terminal_aspect_active,terminal_render_cancel
global ansi_control_character
ansi_control_character:
 jmp terminal_receive_character

global pcplus_seconds,pcplus_flow_bell,pcplus_escape_pressed
pcplus_seconds:
 push cx
 push dx
 mov ah,0x2c
 int 0x21
 xor ax,ax
 mov al,dh
 pop dx
 pop cx
 ret
pcplus_flow_bell:
 push bp
 mov ax,0x0e07
 xor bx,bx
 int 0x10
 pop bp
 ret
pcplus_escape_pressed:
 cmp word [terminal_aspect_active],0
 je .ordinary
 call far terminal_render_cancel
 ret
.ordinary:
 mov ax,[terminal_quit]
 ret
; Real snapshot/flow-message exports now come from reconstruction/ui_windows.
; The live transport continues to use bounded queued writes.
