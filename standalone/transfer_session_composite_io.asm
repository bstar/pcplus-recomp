; Replaceable fixture adapter: scheduled RX frames, bounded memory sink.
; This file alone owns diagnostic UART/time/path/UI/file callback behavior.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern session_queued_count,session_protocol,session_streaming_mode
extern session_buffer_used,session_blocks_accepted,session_total_low
extern session_error_count,session_file_handle

global composite_io_reset
composite_io_reset:
 xor ax,ax
 mov [composite_owner_result],ax
 mov [composite_wire_count],ax
 mov [composite_schedule_next],ax
 mov [composite_input_remaining],ax
 mov [session_queued_count],ax
 mov [composite_file_used],ax
 mov [composite_file_write_calls],ax
 mov [composite_file_close_calls],ax
 mov [composite_status_code],ax
 mov [composite_read_calls],ax
 mov [composite_first_error],ax
 mov [composite_progress_calls],ax
 ret

global composite_transmit_byte
composite_transmit_byte:
 push bp
 mov bp,sp
 push bx
 push si
 mov ax,[bp+4]
 mov bx,[composite_wire_count]
 cmp bx,1024
 jae .overflow
 mov [composite_wire+bx],al
 inc word [composite_wire_count]
 mov bx,[composite_schedule_next]
 cmp bx,[composite_schedule_count]
 jae .done
 mov si,bx
 shl bx,1
 shl si,1
 add bx,si
 add bx,si
 cmp ax,[composite_schedule+bx]
 jne .done
 mov ax,[composite_schedule+bx+2]
 mov [composite_input_pointer],ax
 mov ax,[composite_schedule+bx+4]
 mov [composite_input_remaining],ax
 mov [session_queued_count],ax
 inc word [composite_schedule_next]
.done:
 pop si
 pop bx
 pop bp
 ret 2
.overflow:
 int 3
 jmp .done

global composite_timed_byte,composite_header_byte
composite_timed_byte:
 call composite_header_byte
 ret 2
composite_header_byte:
 inc word [composite_read_calls]
 mov ax,0xffff
 cmp word [composite_input_remaining],0
 je .done
 push bx
 mov bx,[composite_input_pointer]
 xor ax,ax
 mov al,[bx]
 inc word [composite_input_pointer]
 dec word [composite_input_remaining]
 dec word [session_queued_count]
 pop bx
.done:
 ret

global composite_flush_input,composite_delay_ticks,composite_local_cancel
composite_flush_input:
 mov word [composite_input_remaining],0
 mov word [session_queued_count],0
 ret
composite_delay_ticks: ret 2
composite_local_cancel:
 xor ax,ax
 cmp word [composite_cancel_after_reads],0
 je .done
 mov ax,[composite_read_calls]
 cmp ax,[composite_cancel_after_reads]
 mov ax,0
 jb .done
 inc ax
.done: ret

global composite_carrier_present,composite_clock,composite_status
composite_carrier_present:
 mov ax,[composite_carrier]
 ret
composite_clock:
 mov ax,0x1234
 mov dx,0
 ret
composite_status:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [composite_status_code],ax
 pop bp
 ret

global composite_progress,composite_file_open,composite_file_write
composite_progress:
 inc word [composite_progress_calls]
 ret
composite_file_open:
 mov ax,1
 ret
composite_file_write:
 push bp
 mov bp,sp
 push si
 push di
 push es
 inc word [composite_file_write_calls]
 mov ax,[composite_write_fail_call]
 cmp ax,[composite_file_write_calls]
 je .failed
 cmp word [bp+8],1
 jne .failed
 cmp word [bp+10],1
 jne .failed
 mov cx,[bp+6]
 mov ax,cx
 add ax,[composite_file_used]
 jc .failed
 cmp ax,14000
 ja .failed
 mov [composite_file_used],ax
 mov si,[bp+4]
 mov di,[composite_file_used]
 sub di,cx
 add di,composite_file_data
 push ds
 pop es
 cld
 rep movsb
 mov ax,1
 jmp .done
.failed:
 mov word [composite_first_error],1
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

global composite_file_close,composite_setflow,composite_timestamp
composite_file_close:
 inc word [composite_file_close_calls]
 xor ax,ax
 cmp word [composite_close_fail],0
 je .done
 mov word [composite_first_error],2
 mov ax,0xffff
.done: ret
composite_setflow: ret
composite_timestamp: ret

global composite_path_test,composite_display_path,composite_ui_print
composite_path_test:
 xor ax,ax
 ret
composite_display_path:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 pop bp
 ret
composite_ui_print: ret 6

global composite_unsupported
composite_unsupported:
 int 3
 ret

; Actual DOS fixture: one valid all-zero checksum block, then EOT, repeatedEOT.
; Trigger NAK delays initial arrival until native checksum fallback.
global composite_prepare_dos
composite_prepare_dos:
 mov word [session_protocol],4
 mov word [composite_schedule_count],3
 mov word [composite_schedule],0x15
 mov word [composite_schedule+2],composite_input_data
 mov word [composite_schedule+4],132
 mov word [composite_schedule+6],6
 mov word [composite_schedule+8],composite_input_data+132
 mov word [composite_schedule+10],1
 mov word [composite_schedule+12],0x15
 mov word [composite_schedule+14],composite_input_data+133
 mov word [composite_schedule+16],1
 mov byte [composite_input_data],1
 mov byte [composite_input_data+1],1
 mov byte [composite_input_data+2],254
 mov byte [composite_input_data+131],0
 mov byte [composite_input_data+132],4
 mov byte [composite_input_data+133],4
 ret
global composite_dos_assert
composite_dos_assert:
 cmp word [composite_owner_result],1
 jne .fail
 cmp word [composite_first_error],0
 jne .fail
 cmp word [composite_file_used],128
 jne .fail
 cmp word [composite_file_close_calls],1
 jne .fail
 cmp word [session_blocks_accepted],1
 jne .fail
 xor ax,ax
 ret
.fail:
 mov ax,1
 ret

SEGMENT _DATA public class=DATA use16
global composite_owner_result,composite_test_filename
composite_owner_result: dw 0
composite_test_filename: db 'TEST.BIN',0
global composite_schedule_count,composite_schedule_next,composite_schedule
composite_schedule_count: dw 0
composite_schedule_next: dw 0
composite_schedule: times 128*3 dw 0
global composite_input_data,composite_input_pointer,composite_input_remaining
composite_input_data: times 16000 db 0
composite_input_pointer: dw 0
composite_input_remaining: dw 0
global composite_wire,composite_wire_count
composite_wire: times 1024 db 0
composite_wire_count: dw 0
global composite_file_used,composite_file_data,composite_file_write_calls
composite_file_used: dw 0
composite_file_data: times 14000 db 0
composite_file_write_calls: dw 0
global composite_file_close_calls,composite_first_error,composite_write_fail_call
composite_file_close_calls: dw 0
composite_first_error: dw 0
composite_write_fail_call: dw 0
global composite_close_fail,composite_status_code,composite_progress_calls
composite_close_fail: dw 0
composite_status_code: dw 0
composite_progress_calls: dw 0
global composite_read_calls,composite_cancel_after_reads,composite_carrier
composite_read_calls: dw 0
composite_cancel_after_reads: dw 0
composite_carrier: dw 1
