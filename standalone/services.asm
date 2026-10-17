; Minimal host services for the independent serial diagnostic, not PCPlus UI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global pcplus_seconds, pcplus_flow_bell, pcplus_flow_message
 global pcplus_escape_pressed, pcplus_screen_restore, pcplus_screen_save
pcplus_seconds:
 ; Original 0x3323/0x778c returns DOS seconds (0..59), not BIOS ticks.
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
 ret
pcplus_flow_message:
 ; Caller removes its two arguments. Diagnostic has no saved-screen UI.
 ret
pcplus_screen_restore:
pcplus_screen_save:
 ; Original screen helpers remove their three arguments.
 ret 6
pcplus_escape_pressed:
 ; Keyboard exit is handled by the diagnostic's main loop. Do not eat keys.
 xor ax,ax
 ret
