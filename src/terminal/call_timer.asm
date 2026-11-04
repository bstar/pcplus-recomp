; Live call-clock lifecycle around the exact recovered resident timer bodies.
; A dedicated retained bank leaves the near resident segment unchanged.
BITS 16
CPU 8086
%ifdef TERMINAL_CALL_TIMER
SEGMENT ELAPSED_TIMER_CODE public align=16 class=FARCODE use16
GROUP ELAPSED_TIMER_GROUP ELAPSED_TIMER_CODE
extern elapsed_start,elapsed_update
extern elapsed_start_seconds
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
%endmacro
%macro restore 0
 pop es
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
global terminal_call_timer_start_far,terminal_call_timer_stop_far,terminal_call_timer_refresh_far
terminal_call_timer_start_far:
 save
 cmp word [terminal_call_timer_running],0
 jne .done
 call elapsed_start
 mov word [terminal_call_timer_running],1
 mov word [terminal_call_timer_valid],1
 inc word [terminal_call_timer_epoch]
.done:
 restore
terminal_call_timer_stop_far:
 save
 cmp word [terminal_call_timer_running],0
 je .done
 call elapsed_update
 mov word [terminal_call_timer_running],0
.done:
 restore
terminal_call_timer_refresh_far:
 save
 cmp word [terminal_call_timer_running],0
 je .done
 call elapsed_update
.done:
 restore

; Original callee-cleaned time-structure ABI, now bound to DOS AH2C.
; DS=SS; DOS supplies CH=hour,CL=minute,DH=second,DL=hundredths.
global elapsed_gettime
elapsed_gettime:
 push bp
 mov bp,sp
 push bx
 mov bx,[bp+4]
 mov ah,0x2c
 int 0x21
 xor ax,ax
 mov al,dl
 mov [bx],ax
 mov al,ch
 mov [bx+2],ax
 mov al,cl
 mov [bx+4],ax
 mov al,dh
 mov [bx+6],ax
 pop bx
 pop bp
 ret 2

; Narrow adapters for the native timer's proven nonnegative <86400 operands.
; Unlike general CRT long division, the divisor here is always60 or3600.
global elapsed_divide,elapsed_remainder
elapsed_divide:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov dx,[bp+6]
 div word [bp+8]
 xor dx,dx
 pop bp
 ret 8
elapsed_remainder:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov dx,[bp+6]
 div word [bp+8]
 mov ax,dx
 xor dx,dx
 pop bp
 ret 8

; Fixed %2.2d:%2.2d:%2.2d timer formatter; not a general sprintf replacement.
global elapsed_sprintf
elapsed_sprintf:
 push bp
 mov bp,sp
 push bx
 push di
 mov di,[bp+4]
 mov bx,10
 mov ax,[bp+8]
 call .pair
 mov byte [di],':'
 inc di
 mov ax,[bp+10]
 call .pair
 mov byte [di],':'
 inc di
 mov ax,[bp+12]
 call .pair
 mov byte [di],0
 mov ax,8
 pop di
 pop bx
 pop bp
 ret
.pair:
 xor dx,dx
 div bx
 add al,'0'
 mov [di],al
 inc di
 mov al,dl
 add al,'0'
 mov [di],al
 inc di
 ret

SEGMENT _DATA public class=DATA use16
global terminal_call_timer_running,terminal_call_timer_valid,terminal_call_timer_epoch
terminal_call_timer_running: dw 0
terminal_call_timer_valid: dw 0
terminal_call_timer_epoch: dw 0
global elapsed_start_stamp,elapsed_start_seconds,elapsed_hours,elapsed_minutes,elapsed_secs
global elapsed_duration,elapsed_format
elapsed_start_stamp: times 8 db 0
elapsed_start_seconds: dd 0
elapsed_hours: dw 0
elapsed_minutes: dw 0
elapsed_secs: dw 0
elapsed_duration: db '00:00:00',0
elapsed_format: db '%2.2d:%2.2d:%2.2d',0
%endif
