; Maintained live sender initialization/state, independent of receiver counters.
; Exclusive owner shares only session_payload arena and actual UART RX count.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern transfer_send_session,session_payload
GLOBAL _terminal_transfer_send,send_reset_state,_terminal_upload_native_prepare
_terminal_transfer_send:
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
.scan:
 mov al,[si]
 or al,al
 jz .valid
 cmp al,13
 je .invalid
 cmp al,10
 je .invalid
 inc cx
 cmp cx,64
 jae .invalid
 inc si
 jz .invalid
 jmp .scan
.valid:
 or cx,cx
 jz .invalid
 push word [bp+4]
 call transfer_send_session
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

; Real native reset callback. No file/UART/UI IO. Source-owned init deliberately
; fixes protocol2 ordinary XMODEM/1K; never indexes an original baud/profiletable.
; Root preflight filesize is outside the clear region and copied, not inferred.
_terminal_upload_native_prepare:
send_reset_state:
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 pop es
 mov di,terminal_upload_native_state_begin
 mov cx,(terminal_upload_native_state_end-terminal_upload_native_state_begin)/2
 xor ax,ax
 cld
 rep stosw
 mov word [send_protocol],2
 mov word [send_ui_context],7
 mov word [send_buffer_pointer],session_payload
 mov byte [send_directory_prefix],0
 mov ax,[terminal_upload_file_size_low]
 mov [send_file_size_low],ax
 mov ax,[terminal_upload_file_size_high]
 mov [send_file_size_high],ax
 xor ax,ax
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
SEGMENT _DATA public class=DATA use16
GLOBAL terminal_upload_file_size_low,terminal_upload_file_size_high
GLOBAL _terminal_upload_file_size_low,_terminal_upload_file_size_high
_terminal_upload_file_size_low:
terminal_upload_file_size_low: dw 0
_terminal_upload_file_size_high:
terminal_upload_file_size_high: dw 0
GLOBAL terminal_upload_native_state_begin,terminal_upload_native_state_end
terminal_upload_native_state_begin:
global send_ui_context
send_ui_context:
 dw 0
global send_protocol
send_protocol:
 dw 0
global send_buffer_pointer
send_buffer_pointer:
 dw 0
global send_total_low
send_total_low:
 dw 0
global send_total_high
send_total_high:
 dw 0
global send_file_size_low
send_file_size_low:
 dw 0
global send_file_size_high
send_file_size_high:
 dw 0
global send_session_low
send_session_low:
 dw 0
global send_session_high
send_session_high:
 dw 0
global send_block_size
send_block_size:
 dw 0
global send_file_handle
send_file_handle:
 dw 0
global send_crc_high
send_crc_high:
 dw 0
global send_crc_low
send_crc_low:
 dw 0
global send_block_number
send_block_number:
 dw 0
global send_buffer_used
send_buffer_used:
 dw 0
global send_blocks_counted
send_blocks_counted:
 dw 0
global send_error_count
send_error_count:
 dw 0
global send_checkpoint_buffer
send_checkpoint_buffer:
 times 10 db 0
global send_streaming_mode
send_streaming_mode:
 dw 0
terminal_upload_native_state_end:
global send_directory_prefix,send_initial_open_mode,send_binary_open_mode,send_integrity_labels
send_directory_prefix: db 0
send_initial_open_mode: db 'r',0
send_binary_open_mode: db 'rb',0
send_integrity_labels: dw upload_checksum_label,upload_crc_label,upload_wait_label
upload_checksum_label: db 'Checksum',0
upload_crc_label: db 'CRC',0
upload_wait_label: db 'Wait',0
