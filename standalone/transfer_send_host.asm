; Declared synthetic memory FILE/UART/UI fixture, never a live transfer service.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern transfer_send_session,send_unwind
GLOBAL _transfer_send_dos_test
_transfer_send_dos_test:
 mov ax,send_payload_buffer
 mov [send_buffer_pointer],ax
 mov word [send_protocol],4
 mov word [fixture_carrier],1
 mov word [fixture_file_length],3
 mov word [fixture_script_count],3
 mov word [fixture_script],0x15
 mov word [fixture_script+2],6
 mov word [fixture_script+4],6
 mov ax,fixture_filename
 push ax
 call transfer_send_session
 pop bx
 cmp ax,1
 jne .bad
 cmp word [fixture_wire_count],133
 jne .bad
 cmp byte [fixture_wire],1
 jne .bad
 cmp byte [fixture_wire+1],1
 jne .bad
 cmp byte [fixture_wire+2],0xfe
 jne .bad
 cmp byte [fixture_wire+3],'A'
 jne .bad
 cmp byte [fixture_wire+131],120
 jne .bad
 cmp byte [fixture_wire+132],4
 jne .bad
 cmp word [send_blocks_counted],1
 jne .bad
 xor ax,ax
 ret
.bad: mov ax,1
 ret

global send_timed_byte,send_header_byte,send_receive_byte
send_timed_byte:
 inc word [fixture_timed_calls]
 mov bx,sp
 mov ax,[ss:bx+2]
 mov [fixture_last_timeout],ax
 call fixture_next_byte
 ret 2
send_header_byte:
send_receive_byte:
 call fixture_next_byte
 ret
fixture_next_byte:
 mov bx,[fixture_script_index]
 cmp bx,[fixture_script_count]
 jae .empty
 inc word [fixture_script_index]
 shl bx,1
 mov ax,[fixture_script+bx]
 ret
.empty: mov ax,0xffff
 ret

global send_transmit_byte,send_transmit_buffer
send_transmit_byte:
 mov bx,sp
 mov al,[ss:bx+2]
 call fixture_capture
 ret 2
fixture_capture:
 mov bx,[fixture_wire_count]
 cmp bx,20000
 jae .overflow
 mov [fixture_wire+bx],al
 inc word [fixture_wire_count]
 ret
.overflow: int 3
 ret
send_transmit_buffer:
 push bp
 mov bp,sp
 push si
 mov cx,[bp+4]
 mov si,[bp+6]
.loop: jcxz .done
 lodsb
 call fixture_capture
 loop .loop
.done: pop si
 pop bp
 ret 4

global send_open_file,send_read_file,send_close_file
send_open_file:
 mov ax,[fixture_open_error]
 or ax,ax
 jnz .failed
 mov ax,1
 ret
.failed: xor ax,ax
 ret
send_close_file:
 inc word [fixture_close_count]
 xor ax,ax
 ret
send_read_file:
 cmp word [fixture_read_error],0
 je .normal
 mov ax,0xffff
 ret
.normal:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov si,[fixture_file_index]
 mov cx,[fixture_file_length]
 sub cx,si
 cmp cx,[bp+8]
 jbe .size
 mov cx,[bp+8]
.size:
 mov ax,cx
 add [fixture_file_index],ax
 add si,fixture_file
 mov di,[bp+4]
 push ds
 pop es
 cld
 rep movsb
 pop es
 pop di
 pop si
 pop bp
 ret

global send_local_cancel,send_carrier,send_status,send_flush_input
send_local_cancel: mov ax,[fixture_cancel]
 ret
send_carrier: mov ax,[fixture_carrier]
 ret
send_status: mov bx,sp
 mov ax,[ss:bx+2]
 mov [fixture_status],ax
 ret
send_flush_input: inc word [fixture_flush_count]
 ret
; UI/progress boundaries are intentional recording/no-display fixtures.
global send_reset_state,send_prepare_ui,send_filename_display,send_display_text,send_display_start,send_initialize_progress,send_progress
send_reset_state:
send_prepare_ui:
send_display_start:
send_initialize_progress:
send_progress: ret
send_filename_display: mov ax,fixture_filename
 ret
send_display_text: ret 6
; Alternate protocol/metadata boundaries deliberately fail; never claim transfer.
global send_delegate_protocol13,send_delegate_U,send_delegate_W,send_metadata3,send_metadata5
send_delegate_protocol13:
send_delegate_U:
send_delegate_W:
send_metadata3:
send_metadata5: xor ax,ax
 ret
SEGMENT _DATA public class=DATA use16
global send_protocol
send_protocol: dw 0
global send_buffer_pointer
send_buffer_pointer: dw 0
global send_ui_context
send_ui_context: dw 0
global send_integrity_labels
send_integrity_labels: times 3 dw 0
global send_initial_open_mode
send_initial_open_mode: dw 0
global send_binary_open_mode
send_binary_open_mode: dw 0
global send_queued_count
send_queued_count: dw 0
global send_total_low
send_total_low: dw 0
global send_total_high
send_total_high: dw 0
global send_file_size_low
send_file_size_low: dw 0
global send_file_size_high
send_file_size_high: dw 0
global send_session_low
send_session_low: dw 0
global send_session_high
send_session_high: dw 0
global send_block_size
send_block_size: dw 0
global send_file_handle
send_file_handle: dw 0
global send_crc_high
send_crc_high: dw 0
global send_crc_low
send_crc_low: dw 0
global send_block_number
send_block_number: dw 0
global send_buffer_used
send_buffer_used: dw 0
global send_blocks_counted
send_blocks_counted: dw 0
global send_error_count
send_error_count: dw 0
global send_streaming_mode
send_streaming_mode: dw 0
global send_checkpoint_buffer
send_checkpoint_buffer: times 5 dw 0
global send_directory_prefix
send_directory_prefix: times 66 db 0
global fixture_filename,fixture_script,fixture_script_count,fixture_script_index,fixture_wire,fixture_wire_count,fixture_file,fixture_file_length,fixture_file_index,fixture_status,fixture_carrier,fixture_cancel,fixture_close_count,fixture_flush_count
fixture_filename: db 'OWNED.BIN',0
fixture_script_count: dw 0
fixture_script_index: dw 0
fixture_script: times 1024 dw 0
fixture_wire_count: dw 0
fixture_wire: times 20000 db 0
fixture_file_length: dw 0
fixture_file_index: dw 0
fixture_file: db 'ABC'
 times 10237 db 0
fixture_status: dw 0
fixture_carrier: dw 0
fixture_cancel: dw 0
fixture_close_count: dw 0
fixture_flush_count: dw 0
global send_payload_buffer
send_payload_buffer: times 10240 db 0

global fixture_timed_calls,fixture_last_timeout,fixture_open_error,fixture_read_error
fixture_timed_calls: dw 0
fixture_last_timeout: dw 0
fixture_open_error: dw 0
fixture_read_error: dw 0
