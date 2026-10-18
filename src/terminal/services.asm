; Maintained runtime providers for recovered input and driver services.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_receive_character,terminal_quit,terminal_abort
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
 mov ax,[terminal_quit]
 ret
; The interactive host uses bounded queued writes, never the old modal flow UI.
; If an unreconstructed path reaches that UI it must unwind, not fake success.
global pcplus_flow_message,pcplus_screen_restore,pcplus_screen_save
pcplus_flow_message:
 mov ax,0xfff0
 jmp terminal_abort
pcplus_screen_restore:
 mov ax,0xfff1
 jmp terminal_abort
pcplus_screen_save:
 mov ax,0xfff2
 jmp terminal_abort
