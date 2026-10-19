; DS=SS near/far adapters for the recovered status owner. No parser substitute.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
extern terminal_reset_status_refresh,_status_format,status_error
global status_renderer_refresh
status_renderer_refresh:
 mov word [status_error],0
 call terminal_reset_status_refresh
 mov ax,[status_error]
 retf

; Native75E8 owns136 bytes; native2FB8's alternate format owns92 bytes.
; Both pass stack words with near string pointers in the current DS=SS.
global status_sprintf,terminal_reset_sprintf
status_sprintf:
 mov cx,136
 mov dx,12
 jmp short status_format_call
terminal_reset_sprintf:
 mov cx,92
 mov dx,8
status_format_call:
 push bp
 mov bp,sp
 lea ax,[bp+8]
 push dx
 push ax
 push word [bp+6]
 push cx
 push word [bp+4]
 call far _status_format
 lea sp,[bp]
 or ax,ax
 jns .done
 mov bx,7
 cmp ax,-2
 jne .args
 mov bx,3
.args:
 cmp ax,-3
 jne .error
 mov bx,10
.error:
 mov [status_error],bx
.done:
 pop bp
 ret

; CONFIG near callee-cleaned -> resident far adapter -> real native near.
; The resident frame retains both the far return and CONFIG's near return.
%macro status_far_service 2
 extern %1 %+ _resident
 global %1
%1:
 call far %1 %+ _resident
 ret %2*2
%endmacro
status_far_service status_text_fill,3
status_far_service status_text_packed,2
status_far_service status_write_string,3
extern status_strlen_resident,status_uart_resident
global status_strlen,terminal_reset_uart_status
status_strlen:
 call far status_strlen_resident
 ret
terminal_reset_uart_status:
 call far status_uart_resident
 ret

SEGMENT _TEXT public class=CODE use16
%macro status_near_service 3
 extern %2
 global %1 %+ _resident
%1 %+ _resident:
 push bp
 mov bp,sp
 %assign %%arg %3-1
 %rep %3
  push word [bp+8+2*%%arg]
  %assign %%arg %%arg-1
 %endrep
 call %2
 lea sp,[bp]
 pop bp
 retf
%endmacro
status_near_service status_text_fill,text_fill_cells,3
status_near_service status_text_packed,text_write_packed,2
status_near_service status_write_string,ui_write_string,3
status_near_service status_strlen,program_strlen,1
extern status_carrier_read
global status_uart_resident
status_uart_resident:
 call status_carrier_read
 retf
