; Small maintained connection notice using the recovered window services.
; SI=NUL string of at most14 bytes. No delay/keyboard/serial service is called.
; The first15 bottom-row cells are restored before online data is rendered.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern pcplus_screen_save,pcplus_screen_restore,pcplus_flow_message
extern terminal_redisplay_stop
global terminal_connection_notice,terminal_connection_notice_restore
%macro save 0
 push bp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 ret
%endmacro
terminal_connection_notice:
 save
 ; Notices own the live screen, never a cached history-page underlay.
 call terminal_redisplay_stop
 cmp byte [notice_active],0
 jne .draw
 mov ax,notice_cells
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_save
 mov byte [notice_active],1
.draw:
 xor ax,ax
 push ax
 push si
 call pcplus_flow_message
 add sp,4
 restore
terminal_connection_notice_restore:
 save
 cmp byte [notice_active],0
 je .done
 mov ax,notice_cells
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_restore
 mov byte [notice_active],0
.done:
 restore
SEGMENT _DATA public class=DATA use16
notice_active: db 0
notice_cells: times 30 db 0
