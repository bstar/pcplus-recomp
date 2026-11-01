; Far no-argument entries preserve registers, flags and the parent's DS=SS.
BITS 16
CPU 8086
%ifdef TERMINAL_SOUND
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%macro alert_entry 1
 extern _terminal_connect_alert_ %+ %1 %+ _impl
 global terminal_connect_alert_ %+ %1
 terminal_connect_alert_ %+ %1:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cld
 call _terminal_connect_alert_ %+ %1 %+ _impl
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
%endmacro
alert_entry initialize
alert_entry start
alert_entry poll
alert_entry stop
%endif
