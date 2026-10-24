bits 16
cpu 8086
segment _TEXT public class=CODE use16
extern phone_log_native,_phone_log_notice_impl
global _phone_log_call,phone_log_notice
_phone_log_call:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push word [bp+4]
 call phone_log_native
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
phone_log_notice:
 push bx
 call _phone_log_notice_impl
 pop bx
 ret
