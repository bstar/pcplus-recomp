BITS 16
CPU 8086
%ifdef TERMINAL_SESSION_PROJECTION
%include "far_bridge.inc"
SEGMENT _TEXT public class=CODE use16
NEAR_NAMED_SERVICE hook_memcpy_service_,memcpy_
NEAR_NAMED_SERVICE hook_memcmp_service_,memcmp_
NEAR_CDECL_SERVICE _hook_terminal_decode,_terminal_import_decode,2
NEAR_CDECL_SERVICE _hook_modem_decode,_modem_import_decode,2
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
NEAR_CDECL_SERVICE _hook_transfer_decode,_transfer_import_decode,2
NEAR_CDECL_SERVICE _hook_transfer_path,_transfer_import_path,2
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
%macro HOOK_REGISTER 1
 global %1
 extern %1 %+ _resident
 %1:
 call far %1 %+ _resident
 ret
%endmacro
HOOK_REGISTER hook_memcpy_service_
HOOK_REGISTER hook_memcmp_service_
FAR_CDECL_SERVICE _hook_terminal_decode,_terminal_import_decode,2
FAR_CDECL_SERVICE _hook_modem_decode,_modem_import_decode,2
FAR_CDECL_SERVICE _hook_transfer_decode,_transfer_import_decode,2
FAR_CDECL_SERVICE _hook_transfer_path,_transfer_import_path,2
extern terminal_session_capture_far
global _hook_session_capture,_hook_rate_index
_hook_session_capture:
 push bp
 mov bp,sp
 push bx
 push dx
 mov ax,[bp+4]
 mov dx,[bp+6]
 mov bx,1
 call far terminal_session_capture_far
 pop dx
 pop bx
 pop bp
 ret
; Code-resident rate table keeps DGROUP unchanged. Same native rate order as
; terminal_import.c; independent linked tests cover every low/high-word pair.
_hook_rate_index:
 push bp
 mov bp,sp
 push si
 push cx
 push dx
 mov dx,[bp+4]
 mov cx,[bp+6]
 xor ax,ax
 mov si,.rates
.loop:
 cmp dx,[cs:si]
 jne .next
 cmp cx,[cs:si+2]
 je .done
.next:
 add si,4
 inc ax
 cmp ax,9
 jb .loop
.done:
 pop dx
 pop cx
 pop si
 pop bp
 ret
.rates: dd 300,1200,2400,4800,9600,19200,38400,57600,115200
%endif
