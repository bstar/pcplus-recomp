; Source-owned bounded session diagnostic. UART/time/keyboard/UI are explicit
; fixture boundaries. Native setjmp/longjmp and double-CAN helpers execute.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern session_initialize,session_totals_initialize,session_handshake_enter
extern session_retry_enter,session_wait,session_setjmp,session_longjmp
extern receive_control_status
%include "session_externs.inc"
global _transfer_session_probe,_transfer_session_dos_test
_transfer_session_probe:
 push bp
 mov bp,sp
 sub sp,0x58
 push di
 push si
 mov word [session_status_code],0
 mov word [session_wire_count],0
 mov word [session_delay_calls],0
 mov word [session_close_calls],0
 mov word [session_ui_calls],0
 mov word [session_timed_calls],0
 mov word [session_probe_returned],0
 mov ax,[bp+4]
 cmp ax,0
 je .handshake
 cmp ax,1
 je .retry
 cmp ax,2
 je .wait
 cmp ax,3
 je .initialize
 cmp ax,4
 je .context
 mov ax,0xfffe
 jmp .return
.handshake:
 jmp session_handshake_enter
.retry:
 mov word [bp-14h],0
 mov ax,[session_probe_retries]
 mov [bp-14h],ax
 mov word [bp-10h],0xffff
 jmp session_context_entry
.wait:
 call session_wait
 jmp .return
.initialize:
 call session_initialize
 call session_totals_initialize
 xor ax,ax
 jmp .return
.context:
 mov si,0x1357
 mov di,0x2468
 mov ax,session_context
 push ax
 call session_setjmp
 add sp,2
 or ax,ax
 jnz .context_resumed
 push word [session_probe_jump_value]
 mov ax,session_context
 push ax
 mov si,0xffff
 mov di,0xffff
 sub sp,20
 ; Supply args from current stack so the actual longjmp must restore SP.
 add sp,20
 call session_longjmp
 mov word [session_probe_returned],1
.context_resumed:
 mov [session_probe_si],si
 mov [session_probe_di],di
 jmp .return
.return:
 mov [session_probe_crc],di
 pop si
 pop di
 mov sp,bp
 pop bp
 ret

; Entry alias supplied to isolate retry from handshake while running real
; context capture/result dispatch. This jump does not replace a product helper.
global session_context_entry
extern session_context_enter
session_context_entry: jmp session_context_enter

global session_header_checkpoint,session_retry_limit,session_file_cleanup_checkpoint
session_header_checkpoint:
 xor ax,ax
 jmp _transfer_session_probe.return
session_retry_limit:
 mov ax,15
 jmp _transfer_session_probe.return
session_file_cleanup_checkpoint:
 mov ax,[bp-12h]
 add ax,0x100
 jmp _transfer_session_probe.return

global session_protocol9_boundary,session_protocol12_boundary
session_protocol9_boundary: mov ax,0x9009
 ret
session_protocol12_boundary: mov ax,0x900c
 ret

global session_local_cancel,session_carrier_present,session_delay_ticks
session_local_cancel: mov ax,[session_cancel_requested]
 ret
session_carrier_present: mov ax,[session_carrier]
 ret
session_delay_ticks:
 push bp
 mov bp,sp
 inc word [session_delay_calls]
 mov ax,[session_arrival_delay]
 or ax,ax
 jz .done
 cmp ax,[session_delay_calls]
 jne .done
 mov word [session_queued_count],1
.done:
 pop bp
 ret 2

global session_clock,session_status,session_ui_print,session_transmit_byte
session_clock:
 mov ax,0x1234
 mov dx,0x5678
 ret
session_status:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [session_status_code],ax
 pop bp
 ret
session_ui_print:
 inc word [session_ui_calls]
 ret 6
session_transmit_byte:
 push bp
 mov bp,sp
 push bx
 mov bx,[session_wire_count]
 cmp bx,128
 jae .full
 mov ax,[bp+4]
 mov [session_wire+bx],al
 inc word [session_wire_count]
.full:
 pop bx
 pop bp
 ret 2

global session_send_nak,session_timed_byte,session_control_status
session_send_nak:
 mov ax,0x15
 push ax
 call session_transmit_byte
 ret
session_timed_byte:
 inc word [session_timed_calls]
 mov ax,[session_control_byte]
 ret 2
session_control_status: jmp receive_control_status

global receive_longjmp_boundary,receive_header_byte
auto_nonlocal_alias:
receive_longjmp_boundary: jmp session_longjmp
receive_header_byte: mov ax,[session_control_second]
 ret

global session_path_test,session_display_path,session_file_open,session_file_write,session_serial_gate_set
session_path_test:
 mov ax,[session_path_test_result]
 ret
session_display_path:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 pop bp
 ret
session_file_open:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [session_open_path_pointer],ax
 mov ax,[bp+6]
 mov [session_open_mode_pointer],ax
 inc word [session_open_calls]
 mov ax,[session_open_result]
 pop bp
 ret
session_file_write:
 inc word [session_write_calls]
 mov ax,1
 ret
session_serial_gate_set:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [session_serial_gate_value],ax
 pop bp
 ret

global session_file_close_boundary
session_file_close_boundary:
 inc word [session_close_calls]
 xor ax,ax
 ret

_transfer_session_dos_test:
 mov ax,3
 push ax
 call _transfer_session_probe
 add sp,2
 or ax,ax
 jnz .failure
 mov word [session_arrival_delay],1
 mov ax,0
 push ax
 call _transfer_session_probe
 add sp,2
 or ax,ax
 jnz .failure
 cmp word [session_wire_count],1
 jne .failure
 cmp byte [session_wire],0x43
 jne .failure
 mov word [session_probe_jump_value],7
 mov ax,4
 push ax
 call _transfer_session_probe
 add sp,2
 cmp ax,7
 jne .failure
 cmp word [session_probe_si],0x1357
 jne .failure
 mov word [session_streaming_mode],1
 mov word [session_control_byte],0x18
 mov word [session_control_second],0x18
 mov ax,1
 push ax
 call _transfer_session_probe
 add sp,2
 cmp ax,0x107
 jne .failure
 xor ax,ax
 ret
.failure:
 mov ax,1
 ret

SEGMENT _DATA public class=DATA use16
%include "session_state.inc"
global session_context,receive_jump_context
session_context:
receive_jump_context: times 10 db 0
global session_payload
session_payload: times 64 db 0
global session_baud_table,session_baud_table_high
session_baud_table: dw 38400
session_baud_table_high: dw 0
 times 20 dd 0
global session_integrity_labels
session_integrity_labels: dw 0,0
global session_cancel_requested,session_carrier,session_arrival_delay
session_cancel_requested: dw 0
session_carrier: dw 1
session_arrival_delay: dw 0
global session_control_byte,session_control_second,session_probe_retries
session_control_byte: dw 0xffff
session_control_second: dw 0xffff
session_probe_retries: dw 0
global session_status_code,session_wire_count,session_wire,session_delay_calls
session_status_code: dw 0
session_wire_count: dw 0
session_wire: times 128 db 0
session_delay_calls: dw 0
global session_close_calls,session_ui_calls,session_timed_calls
session_close_calls: dw 0
session_ui_calls: dw 0
session_timed_calls: dw 0
global session_probe_jump_value,session_probe_si,session_probe_di,session_probe_returned
session_probe_jump_value: dw 7
session_probe_si: dw 0
session_probe_di: dw 0
session_probe_returned: dw 0

global session_download_prefix,session_open_mode,session_test_filename
session_download_prefix: times 80 db 0
session_open_mode: db 'wb',0
session_test_filename: db 'TEST.BIN',0
global session_open_calls,session_write_calls,session_path_test_result,session_open_result
session_open_calls: dw 0
session_write_calls: dw 0
session_path_test_result: dw 0
session_open_result: dw 3
global session_open_path_pointer,session_open_mode_pointer,session_serial_gate_value
session_open_path_pointer: dw 0
session_open_mode_pointer: dw 0
session_serial_gate_value: dw 0

global session_probe_crc
session_probe_crc: dw 0
; Explicit unentered unit-diagnostic boundaries for separately composed code.
global session_accept_data,session_batch_metadata_boundary,session_commit_buffer
 global session_commit_partial,session_commit_unknown_size,session_long_remainder
session_accept_data:
session_batch_metadata_boundary:
session_commit_buffer:
session_commit_partial:
session_commit_unknown_size:
session_long_remainder:
 int 3
 ret
