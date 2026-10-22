; Maintained foreground modem connection controller. Not overlay5's modal UI.
; Real UART writes/read path, recovered expansion and matching; bounded polls.
; DS=SS, DF=0. Public start/poll/receive/cancel preserve BP/SI/DI/ES.
BITS 16
CPU 8086
%include "modem_import.inc"
SEGMENT MODEM_CODE public align=16 class=FARCODE use16
GROUP MODEM_GROUP MODEM_CODE
global terminal_modem_code_start
terminal_modem_code_start:
extern terminal_option_mask,terminal_dial_target,terminal_modem_settings
extern terminal_directory_mode
extern terminal_modem_send_start_impl,terminal_modem_send_poll_impl
extern modem_response_slots
extern uart_port_msr,uart_port_mcr
extern terminal_baud_low,terminal_baud_high
extern connection_clipboard_abort_service
extern terminal_quit,terminal_tx_count,terminal_tx_head,terminal_tx_tail
global terminal_connection_prepare_impl,terminal_connection_start_impl
global terminal_connection_poll_impl,terminal_connection_receive_impl,terminal_connection_cancel_impl
global terminal_connection_exit_impl

%macro save 0
 push bp
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop bp
 ret
%endmacro

; Called only after complete C validation, before hardware access.
; Build every outgoing command before any transmission; CF1 means prepare error.
terminal_connection_prepare_impl:
 save
 test word [terminal_option_mask],96
 jz .success
 mov ax,ds
 mov es,ax
 cmp word [terminal_directory_mode],1
 je .find_rate
 mov al,[terminal_modem_settings+MI_PAUSE_CHARACTER]
 mov [terminal_modem_pause],al
 mov si,terminal_modem_settings+MI_INITIALIZATION
 mov di,connection_init
 mov cx,47
 call expand
 jc .done
 mov si,terminal_modem_settings+MI_HANGUP
 mov di,connection_hangup
 mov cx,25
 call expand
 jc .done
 mov di,connection_dial
 mov si,terminal_modem_settings+MI_DIAL_PREFIX
 call append_command
 jc .done
 mov si,terminal_dial_target
 mov cx,64
 call append_text
 jc .done
 mov si,terminal_modem_settings+MI_DIAL_SUFFIX
 call append_command
 jc .done
 mov byte [di],0
 mov si,terminal_modem_settings+MI_RESPONSES
 mov di,modem_response_slots
 mov cx,176
 rep movsb
 call connection_responses_reset_service
 jc .done
.find_rate:
 xor bx,bx
.rate:
 mov ax,[connection_rates+bx]
 cmp ax,[terminal_baud_low]
 jne .next_rate
 mov ax,[connection_rates+bx+2]
 cmp ax,[terminal_baud_high]
 je .rate_found
.next_rate:
 add bx,4
 cmp bx,36
 jb .rate
 mov ax,1
 stc
 jmp .done
.rate_found:
 shr bx,1
 shr bx,1
 mov [connection_baud_index],bx
 mov byte [connection_enabled],1
.success:
 xor ax,ax
 clc
.done:
 restore
; Source known bounded by decoded PRM. DI advances over expanded content only.
append_command:
 mov cx,25
append_text:
 push di
 mov di,connection_scratch
 call expand
 pop di
 jc .return
 mov si,connection_scratch
.copy:
 lodsb
 or al,al
 jz .return
 stosb
 jmp .copy
.return:
 ret
expand:
 mov ax,129
 push ax
 push cx
 push di
 push si
 call connection_expand_service
 pushf
 pop dx
 add sp,8
 push dx
 popf
 ret

terminal_connection_start_impl:
 extern terminal_recording_owned_far
 save
 push ax
 call far terminal_recording_owned_far
 or ax,ax
 pop ax
 jnz .done
 call connection_break_cancel_service
 call connection_macro_cancel_service
 call connection_program_cancel_service
 cmp byte [connection_enabled],0
 je .done
 call connection_clipboard_abort_service
 mov word [terminal_tx_count],0
 mov word [terminal_tx_head],0
 mov word [terminal_tx_tail],0
 cmp word [terminal_directory_mode],1
 jne .modem
 mov word [connection_state],6
 mov word [connection_status],1
 mov byte [connection_carrier_seen],0
 call connection_note_connected_service
 call connection_notice_restore_service
 jmp .done
.modem:
 call connection_uart_clear_service
 call connection_responses_reset_service
 call reset_clock
 mov word [connection_result],0xffff
 mov byte [connection_carrier_seen],0
 mov word [connection_state],1
 mov si,message_initializing
 call connection_notice_service
 mov si,connection_init
 cmp word [terminal_modem_settings+MI_INITIALIZE_CONNECTED],0
 jne .send
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x80
 jz .send
 call start_dial
 jmp .done
.send:
 call terminal_modem_send_start_impl
.done:
 restore

reset_clock:
 call connection_clock_ticks_service
 mov [connection_last_tick],ax
 mov [connection_last_tick+2],dx
 mov word [connection_elapsed],0
 mov word [connection_elapsed+2],0
 ; ceil(seconds *1193182/65536) ticks, exact integer arithmetic.
 mov ax,[terminal_modem_settings+MI_TIMEOUT]
 mov cx,18
 mul cx
 mov bx,ax
 mov cx,dx
 mov ax,[terminal_modem_settings+MI_TIMEOUT]
 mov dx,13534
 mul dx
 add bx,dx
 adc cx,0
 or ax,ax
 jz .ready
 add bx,1
 adc cx,0
.ready:
 mov [connection_deadline],bx
 mov [connection_deadline+2],cx
 ret
start_dial:
 call connection_uart_clear_service
 call connection_responses_reset_service
 mov word [connection_result],0xffff
 mov word [connection_state],2
 mov si,message_dialing
 call connection_notice_service
 mov si,connection_dial
 call terminal_modem_send_start_impl
 ret

terminal_connection_poll_impl:
 save
 cmp word [connection_state],0
 je .done
 cmp word [connection_state],6
 je .carrier
 call connection_clock_ticks_service
 mov cx,ax
 mov bx,dx
 sub ax,[connection_last_tick]
 sbb dx,[connection_last_tick+2]
 jnc .clock_delta
 ; BIOS wraps at 0018:00b0 each midnight, not at a power of two.
 add ax,0x00b0
 adc dx,0x0018
.clock_delta:
 mov [connection_last_tick],cx
 mov [connection_last_tick+2],bx
 add [connection_elapsed],ax
 adc [connection_elapsed+2],dx
 cmp word [connection_state],8
 je .dtr_wait
 cmp word [connection_state],7
 je .abort_send
 mov ax,[connection_elapsed+2]
 cmp ax,[connection_deadline+2]
 ja .timeout
 jb .state
 mov ax,[connection_elapsed]
 cmp ax,[connection_deadline]
 jae .timeout
.state:
 cmp word [connection_state],5
 je .response
 call terminal_modem_send_poll_impl
 or ax,ax
 jz .done
 cmp word [connection_state],1
 jne .sent
 call start_dial
 jmp .done
.sent:
 cmp word [connection_state],9
 je .drop_dtr
 mov word [connection_state],5
 mov si,message_waiting
 call connection_notice_service
.response:
 mov ax,[connection_result]
 cmp ax,0xffff
 je .done
 mov bx,[terminal_modem_settings+MI_AUTOBAUD]
 push bx
 push word [connection_baud_index]
 push ax
 call connection_classify_service
 pushf
 pop cx
 add sp,6
 push cx
 popf
 jc .internal
 or ax,ax
 jz .failure
 mov [connection_baud_index],dx
 or bx,bx
 jz .connected
 mov bx,dx
 shl bx,1
 shl bx,1
 mov ax,[connection_rates+bx]
 mov [terminal_baud_low],ax
 mov dx,[connection_rates+bx+2]
 mov [terminal_baud_high],dx
 push dx
 push ax
 call connection_set_baud_service
 add sp,4
.connected:
 mov word [connection_state],6
 mov word [connection_status],1
 call connection_note_connected_service
 call connection_notice_restore_service
 jmp .done
.carrier:
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x80
 jz .carrier_low
 mov byte [connection_carrier_seen],1
 jmp .done
.carrier_low:
 cmp byte [connection_carrier_seen],0
 je .done
 call connection_break_cancel_service
 call connection_macro_cancel_service
 call connection_program_cancel_service
 mov word [connection_status],6
 mov word [connection_state],0
 call connection_clipboard_abort_service
 mov word [terminal_tx_count],0
 mov word [terminal_tx_head],0
 mov word [terminal_tx_tail],0
 mov si,message_offline
 call connection_notice_service
 jmp .done
.timeout:
 mov word [connection_status],3
 mov si,message_timeout
 call connection_notice_service
 ; A failed online hangup must not inject the dial-abort character into data.
 cmp word [connection_state],9
 je .drop_dtr
 jmp .begin_abort
.failure:
 mov word [connection_status],2
 mov si,message_failed
 call connection_notice_service
 jmp .begin_abort
.internal:
 mov word [connection_status],7
.begin_abort:
 mov word [connection_state],7
 call reset_clock
 jmp .done
.abort_send:
 mov ax,[terminal_modem_settings+MI_ABORT_CHARACTER]
 or al,al
 jz .drop_dtr
 call connection_uart_write_service
 jc .abort_stalled
 jmp .drop_dtr
.abort_stalled:
 ; Cancellation must not block forever behind CTS/XOFF.
 cmp word [connection_elapsed+2],0
 jne .drop_dtr
 cmp word [connection_elapsed],18
 jb .done
.drop_dtr:
 cmp word [terminal_modem_settings+MI_ABORT_DTR],0
 je .finished
 mov dx,[uart_port_mcr]
 in al,dx
 mov [connection_mcr],al
 and al,0xfe
 out dx,al
 mov word [connection_state],8
 mov ax,[connection_elapsed]
 mov [connection_dtr_tick],ax
 jmp .done
.dtr_wait:
 mov ax,[connection_elapsed]
 sub ax,[connection_dtr_tick]
 cmp ax,18
 jb .done
 mov dx,[uart_port_mcr]
 in al,dx
 and al,0xfe
 mov bl,[connection_mcr]
 and bl,1
 or al,bl
 out dx,al
.finished:
 call connection_uart_clear_service
 mov word [connection_state],0
 cmp word [connection_status],5
 jne .done
 mov si,message_disconnected
 call connection_notice_service
.done:
 cmp byte [connection_exit_pending],0
 je .return
 cmp word [connection_state],0
 jne .return
 mov word [terminal_quit],1
.return:
 restore

; AX0 cancels an attempt; AX1 sends configured hangup on an established session.
terminal_connection_cancel_impl:
 extern terminal_recording_owned_far
 save
 push ax
 call far terminal_recording_owned_far
 or ax,ax
 pop ax
 jnz .done
 call connection_break_cancel_service
 call connection_macro_cancel_service
 call connection_program_cancel_service
 cmp byte [connection_enabled],0
 je .done
 cmp word [connection_state],0
 je .done
 cmp word [connection_state],7
 je .done
 cmp word [connection_state],8
 je .done
 call connection_clipboard_abort_service
 mov word [terminal_tx_count],0
 mov word [terminal_tx_head],0
 mov word [terminal_tx_tail],0
 cmp word [terminal_directory_mode],1
 jne .modem
 mov word [connection_state],0
 mov word [connection_status],5
 mov si,message_disconnected
 call connection_notice_service
 jmp .done
.modem:
 mov word [connection_status],4
 mov si,message_cancelled
 call connection_notice_service
 cmp ax,1
 jne .cancel
 cmp word [connection_state],6
 jne .cancel
 mov word [connection_status],5
 mov word [connection_state],9
 mov si,message_hangup
 call connection_notice_service
 mov si,connection_hangup
 call terminal_modem_send_start_impl
 call reset_clock
 jmp .done
.cancel:
 mov word [connection_state],7
 call reset_clock
.done:
 restore

terminal_connection_exit_impl:
 call connection_break_cancel_service
 cmp byte [connection_exit_pending],0
 jne .immediate
 cmp byte [connection_enabled],0
 je .immediate
 cmp word [connection_state],0
 je .immediate
 mov byte [connection_exit_pending],1
 ; Online exit uses the same configured operation as Alt-H. A hangup already
 ; in progress retains its sender/deadline; dialing alone uses abort policy.
 cmp word [connection_state],9
 je .waiting_hangup
 cmp word [connection_state],6
 je .hangup_online
 xor ax,ax
 jmp terminal_connection_cancel_impl
.hangup_online:
 mov ax,1
 jmp terminal_connection_cancel_impl
.waiting_hangup:
 ret
.immediate:
 mov word [terminal_quit],1
 ret

; AL RX byte from actual recovered UART. CF1 consumes modem control traffic;
; CF0 passes online/raw bytes to the ANSI engine. First complete match wins.
terminal_connection_receive_impl:
 save
 cmp word [connection_state],0
 je .pass
 cmp word [connection_state],6
 je .pass
 cmp word [connection_state],2
 jb .consume
 cmp word [connection_state],5
 ja .consume
 cmp word [connection_result],0xffff
 jne .consume
 and ax,255
 push ax
 call connection_responses_feed_service
 pop bx
 jc .bad_matcher
 cmp ax,0xffff
 je .consume
 mov [connection_result],ax
 jmp .consume
.bad_matcher:
 mov word [connection_status],7
 mov word [connection_state],7
 call reset_clock
.consume:
 stc
 jmp .done
.pass:
 clc
.done:
 restore

; All entries and callbacks below are plain near frames inside MODEM_CODE.
%include "far_bridge.inc"
%define MODEM_ENTRY FAR_ENTRY
%define MODEM_SERVICE FAR_NAMED_SERVICE
%define MODEM_CDECL_SERVICE FAR_CDECL_SERVICE
%include "modem_abi.inc"

SEGMENT _DATA public class=DATA use16
global terminal_modem_pause,connection_state,connection_status,connection_result
global connection_enabled,connection_baud_index,connection_elapsed,connection_deadline
terminal_modem_pause: db 0
connection_enabled: db 0
connection_carrier_seen: db 0
connection_mcr: db 0
connection_exit_pending: db 0
connection_state: dw 0
; Status0idle/1online/2responsefailure/3timeout/4cancel/5hangup/6carrierlost/7internal.
connection_status: dw 0
connection_result: dw 0xffff
connection_baud_index: dw 0
connection_last_tick: dd 0
connection_dtr_tick: dw 0
connection_elapsed: dd 0
connection_deadline: dd 0
connection_rates: dd 300,1200,2400,4800,9600,19200,38400,57600,115200
connection_init: times 129 db 0
connection_dial: times 129 db 0
connection_hangup: times 129 db 0
connection_scratch: times 129 db 0
message_initializing: db 'Initializing',0
message_dialing: db 'Dialing',0
message_waiting: db 'Await CONNECT',0
message_timeout: db 'Timed out',0
message_failed: db 'Dial failed',0
message_cancelled: db 'Cancelled',0
message_hangup: db 'Hanging up',0
message_offline: db 'Carrier lost',0
message_disconnected: db 'Disconnected',0
