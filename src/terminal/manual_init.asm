; Maintained bounded send-only owner for the recovered Alt-J contract.
; Retained MODEM bank, DS=SS. Explicit caller-owned output lease; no UI binding.
; Begin: SI=encoded source,CX=capacity1..47,DL=pause marker,AX=total tick budget.
; Poll: AX=0/1 physical-write grant. Cancel: AX=3cancel/7carrier loss/8exit.
; Return AX=status; all other registers and FLAGS preserved. No port/config edits.
BITS 16
CPU 8086
%ifdef TERMINAL_MANUAL_INIT_OWNER
SEGMENT MODEM_CODE public align=16 class=FARCODE use16
GROUP MODEM_GROUP MODEM_CODE
extern connection_clock_ticks_service,connection_uart_write_service,connection_expand_service
extern connection_state,terminal_tx_count
%macro save 0
 pushf
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
 popf
 retf
%endmacro
global terminal_manual_init_begin_far,terminal_manual_init_poll_far,terminal_manual_init_cancel_far
terminal_manual_init_begin_far:
 save
 cmp word [terminal_manual_init_active],0
 jne .busy
 or ax,ax
 jz .invalid
 cmp cx,1
 jb .invalid
 cmp cx,47
 ja .invalid
 cmp word [terminal_tx_count],0
 jne .busy
 cmp word [connection_state],0
 je .expand
 cmp word [connection_state],6
 jne .busy
.expand:
 mov [cs:budget],ax
 mov [cs:pause_marker],dl
 mov ax,129
 push ax
 push cx
 mov ax,manual_payload
 push ax
 push si
 call connection_expand_service
 pushf
 pop dx
 add sp,8
 test dx,1
 jnz .invalid
 mov word [cs:cursor],manual_payload
 mov word [cs:delay],0
 mov word [terminal_manual_init_accepted],0
 mov word [cs:line_open],0
 mov word [terminal_manual_init_status],2
 cmp byte [manual_payload],0
 je .result
 call now
 mov ax,[cs:clock]
 mov dx,[cs:clock+2]
 mov [cs:started],ax
 mov [cs:started+2],dx
 mov [cs:progress],ax
 mov [cs:progress+2],dx
 mov word [terminal_manual_init_status],1
 mov word [terminal_manual_init_active],1
.result:
 mov ax,[terminal_manual_init_status]
 jmp .done
.invalid:
 mov ax,5
 jmp .done
.busy:
 mov ax,6
.done:
 restore

terminal_manual_init_poll_far:
 save
 mov di,ax
 cmp word [terminal_manual_init_active],0
 je .result
 cmp di,1
 ja .invalid
 call now
 mov bx,started
 call elapsed
 or dx,dx
 jnz .timeout
 cmp ax,[cs:budget]
 jae .timeout
 cmp word [cs:delay],0
 je .cursor
 mov bx,paused
 call elapsed
 or dx,dx
 jnz .pause_done
 cmp ax,[cs:delay]
 jb .result
.pause_done:
 mov word [cs:delay],0
 call progress_now
.cursor:
 mov bx,[cs:cursor]
 mov al,[bx]
 or al,al
 jz .complete
 cmp al,[cs:pause_marker]
 je .pause
 mov bx,progress
 call elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jae .timeout
 or di,di
 jz .result
 mov bx,[cs:cursor]
 mov al,[bx]
 cmp al,0xff
 jne .write
 xor al,al
.write:
 call connection_uart_write_service
 jc .result
 mov bx,[cs:cursor]
 inc word [terminal_manual_init_accepted]
 cmp al,13
 jne .not_cr
 mov word [cs:line_open],0
 mov word [terminal_manual_init_needs_resync],0
 jmp .accepted
.not_cr:
 cmp al,10
 je .accepted
 mov word [cs:line_open],1
.accepted:
 inc word [cs:cursor]
 call progress_now
 cmp byte [bx],0xff
 je .result
 mov word [cs:delay],1
 jmp .pause_time
.pause:
 inc word [cs:cursor]
 mov word [cs:delay],10
.pause_time:
 mov ax,[cs:clock]
 mov dx,[cs:clock+2]
 mov [cs:paused],ax
 mov [cs:paused+2],dx
 jmp .result
.complete:
 mov ax,2
 jmp .retire
.timeout:
 mov ax,4
.retire:
 mov [terminal_manual_init_status],ax
 mov word [terminal_manual_init_active],0
 mov word [cs:delay],0
 cmp word [cs:line_open],0
 je .result
 mov word [terminal_manual_init_needs_resync],1
.result:
 mov ax,[terminal_manual_init_status]
 jmp .done
.invalid:
 mov ax,5
.done:
 restore

terminal_manual_init_cancel_far:
 save
 cmp ax,3
 je .valid
 cmp ax,7
 je .valid
 cmp ax,8
 jne .invalid
.valid:
 cmp word [terminal_manual_init_active],0
 je .result
 mov [terminal_manual_init_status],ax
 mov word [terminal_manual_init_active],0
 mov word [cs:delay],0
 cmp word [cs:line_open],0
 je .result
 mov word [terminal_manual_init_needs_resync],1
.result:
 mov ax,[terminal_manual_init_status]
 jmp .done
.invalid:
 mov ax,5
.done:
 restore

now:
 call connection_clock_ticks_service
 mov [cs:clock],ax
 mov [cs:clock+2],dx
 ret
progress_now:
 mov ax,[cs:clock]
 mov dx,[cs:clock+2]
 mov [cs:progress],ax
 mov [cs:progress+2],dx
 ret
; BX=CS-local timestamp. Full-day midnight wrap; no connection-clock writes.
elapsed:
 mov ax,[cs:clock]
 mov dx,[cs:clock+2]
 sub ax,[cs:bx]
 sbb dx,[cs:bx+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done:
 ret
cursor: dw 0
pause_marker: db 0
budget: dw 0
delay: dw 0
line_open: dw 0
clock: dd 0
started: dd 0
progress: dd 0
paused: dd 0
SEGMENT _DATA public class=DATA use16
global terminal_manual_init_active,terminal_manual_init_status,terminal_manual_init_accepted,terminal_manual_init_needs_resync
terminal_manual_init_active: dw 0
terminal_manual_init_status: dw 0 ;0idle,1sending,2sent,3cancel,4timeout; start refuses5invalid/6busy.
terminal_manual_init_accepted: dw 0
terminal_manual_init_needs_resync: dw 0 ;Caller must reconcile partial modem line before retry.
manual_payload: times 129 db 0
%endif
