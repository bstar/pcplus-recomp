; Live native ordinary receiver state; source-owned, no saved original data.
; DS=SS. Queue words compile directly to genuine uart_rx_count in native_link.py.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern session_receive,terminal_baud_low,terminal_baud_high
GLOBAL _terminal_transfer_native_prepare,_terminal_transfer_receive
; No IO. Refresh native RAM state and a single actual-baud DWORD at index0.
_terminal_transfer_native_prepare:
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 pop es
 mov di,terminal_transfer_native_state_begin
 mov cx,(terminal_transfer_native_state_end-terminal_transfer_native_state_begin)/2
 xor ax,ax
 cld
 rep stosw
 mov word [session_protocol],4
 mov word [session_ui_attribute],7
 mov ax,[terminal_baud_low]
 mov [session_baud_table],ax
 mov ax,[terminal_baud_high]
 mov [session_baud_table_high],ax
 xor ax,ax
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
; C-safe wrapper around actual native owner (whose BX is volatile).
; Caller2 filename1..63 plus NUL, explicit validated stage path from owner.
; Native prefix is empty; native stack filename has86 bytes.
_terminal_transfer_receive:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov si,[bp+4]
 or si,si
 jz .invalid
 xor cx,cx
.validate:
 mov al,[si]
 or al,al
 jz .validated
 cmp al,13
 je .invalid
 cmp al,10
 je .invalid
 inc cx
 cmp cx,64
 jae .invalid
 inc si
 jz .invalid
 jmp .validate
.validated:
 or cx,cx
 jz .invalid
 call _terminal_transfer_native_prepare
 push word [bp+4]
 call session_receive
 add sp,2
 jmp .done
.invalid:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GLOBAL terminal_transfer_native_state_begin,terminal_transfer_native_state_end
terminal_transfer_native_state_begin:
global session_baud_index
session_baud_index:
 dw 0
global files_receive_flow_switch
files_receive_flow_switch:
global session_serial_gate
session_serial_gate:
 dw 0
global session_download_prefix
session_download_prefix:
 times 80 db 0
global session_ui_attribute
session_ui_attribute:
 dw 0
global session_short_wait
session_short_wait:
 dw 0
global session_baud_table
session_baud_table:
 dw 0
global session_baud_table_high
session_baud_table_high:
 dw 0
global session_wait_mode
session_wait_mode:
 dw 0
global receive_protocol
receive_protocol:
global session_protocol
session_protocol:
 dw 0
global files_receive_buffer
files_receive_buffer:
global receive_buffer_pointer
receive_buffer_pointer:
global session_buffer_pointer
session_buffer_pointer:
 dw 0
global files_receive_total_low
files_receive_total_low:
global receive_total_low
receive_total_low:
global session_total_low
session_total_low:
 dw 0
global files_receive_total_high
files_receive_total_high:
global receive_total_high
receive_total_high:
global session_total_high
session_total_high:
 dw 0
global files_receive_size_low
files_receive_size_low:
global session_expected_low
session_expected_low:
 dw 0
global files_receive_size_high
files_receive_size_high:
global session_expected_high
session_expected_high:
 dw 0
global session_rate_low
session_rate_low:
 dw 0
global session_rate_high
session_rate_high:
 dw 0
global receive_session_low
receive_session_low:
global session_bytes_low
session_bytes_low:
 dw 0
global receive_session_high
receive_session_high:
global session_bytes_high
session_bytes_high:
 dw 0
global session_state_cb3a
session_state_cb3a:
 dw 0
global session_state_cb54
session_state_cb54:
 dw 0
global session_state_cb56
session_state_cb56:
 dw 0
global receive_block_size
receive_block_size:
 dw 0
global files_receive_stream
files_receive_stream:
global session_file_handle
session_file_handle:
 dw 0
global receive_crc_high
receive_crc_high:
 dw 0
global receive_crc_low
receive_crc_low:
 dw 0
global receive_wire_high
receive_wire_high:
 dw 0
global receive_wire_low
receive_wire_low:
 dw 0
global receive_last_block
receive_last_block:
global session_last_block
session_last_block:
 dw 0
global receive_wire_block
receive_wire_block:
 dw 0
global receive_wire_complement
receive_wire_complement:
 dw 0
global files_receive_used
files_receive_used:
global receive_buffer_used
receive_buffer_used:
global session_buffer_used
session_buffer_used:
 dw 0
global session_state_cd3a
session_state_cd3a:
 dw 0
global session_state_cd76
session_state_cd76:
 dw 0
global session_state_cd7a
session_state_cd7a:
 dw 0
global receive_blocks_accepted
receive_blocks_accepted:
global session_blocks_accepted
session_blocks_accepted:
 dw 0
global receive_error_count
receive_error_count:
global session_error_count
session_error_count:
 dw 0
global receive_jump_context
receive_jump_context:
global session_context
session_context:
 times 10 db 0
global receive_streaming_mode
receive_streaming_mode:
global session_streaming_mode
session_streaming_mode:
 dw 0
global session_started_low
session_started_low:
 dw 0
global session_started_high
session_started_high:
 dw 0
terminal_transfer_native_state_end:
global session_integrity_labels
session_integrity_labels:
 dw terminal_transfer_checksum_label,terminal_transfer_crc_label
global session_open_mode
session_open_mode:
 db 'wb',0
global session_payload
session_payload:
 times 11264 db 0
terminal_transfer_checksum_label: db 'Checksum',0
terminal_transfer_crc_label: db 'CRC',0
