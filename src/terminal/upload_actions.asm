; Maintained live sender adapters: real UART, checked source and actual UI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern transfer_emit,transfer_maybe_unwind,transfer_protocol_started
extern terminal_transfer_fault,terminal_transfer_service
extern terminal_transfer_timed_byte,terminal_transfer_header_byte
extern terminal_transfer_flush_input,terminal_transfer_local_cancel
extern terminal_transfer_carrier_present,terminal_transfer_status
extern terminal_transfer_display_path,terminal_transfer_unsupported
extern terminal_transfer_ui_progress,terminal_transfer_accepted_progress
extern uart_receive_byte,session_payload,send_at_e1ca
extern send_block_size
extern _terminal_upload_open,_terminal_upload_read,_terminal_upload_close

GLOBAL terminal_upload_transmit_byte,terminal_upload_transmit_buffer
terminal_upload_transmit_byte:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 call transfer_emit
 jc .failed
 mov word [transfer_protocol_started],1
.failed:
 call transfer_maybe_unwind
 pop bp
 ret 2
terminal_upload_transmit_buffer:
 push bp
 mov bp,sp
 push cx
 push si
 mov cx,[bp+4]
 cmp cx,128
 je .span
 cmp cx,1024
 jne .invalid
.span:
 mov si,[bp+6]
 cmp si,session_payload
 jb .invalid
 mov ax,si
 add ax,cx
 jc .invalid
 cmp ax,session_payload+10240
 ja .invalid
 cld
.next:
 lodsb
 call transfer_emit
 call transfer_maybe_unwind
 loop .next
 pop si
 pop cx
 pop bp
 ret 4
.invalid:
 jmp terminal_transfer_unsupported ;must unwind, never return through this frame

GLOBAL terminal_upload_timed_byte,terminal_upload_blocks_accepted
terminal_upload_timed_byte:
 push bp
 mov bp,sp
 push word [bp+4]
 call terminal_transfer_timed_byte
 cmp ax,6
 jne .done
 ; Alias is a JMP: the return IP still identifies the real native wait.
 ; Native counts the fifteenth failed attempt too; never use that as an ACK.
 cmp word [bp+2],send_at_e1ca
 jne .done
 inc word [terminal_upload_blocks_accepted]
 push bx
 mov bx,[send_block_size]
 add [terminal_upload_accepted_bytes],bx
 adc word [terminal_upload_accepted_bytes+2],0
 pop bx
 call terminal_transfer_accepted_progress
.done:
 pop bp
 ret 2

GLOBAL terminal_upload_prepare_ui,terminal_upload_display_start
GLOBAL terminal_upload_initialize_progress,terminal_upload_progress
terminal_upload_prepare_ui:
terminal_upload_display_start:
terminal_upload_initialize_progress:
terminal_upload_progress:
 call terminal_transfer_ui_progress
 call terminal_transfer_service
 call transfer_maybe_unwind
 ret
GLOBAL terminal_upload_display_text
terminal_upload_display_text:
 call terminal_transfer_ui_progress
 ret 6
GLOBAL terminal_upload_open_file,terminal_upload_read_file,terminal_upload_close_file
terminal_upload_open_file: jmp _terminal_upload_open
terminal_upload_read_file: jmp _terminal_upload_read
terminal_upload_close_file: jmp _terminal_upload_close
GLOBAL terminal_upload_header_byte,terminal_upload_receive_byte
GLOBAL terminal_upload_flush_input,terminal_upload_local_cancel,terminal_upload_carrier
GLOBAL terminal_upload_status,terminal_upload_filename_display,terminal_upload_unsupported
terminal_upload_header_byte: jmp terminal_transfer_header_byte
terminal_upload_receive_byte: jmp uart_receive_byte
terminal_upload_flush_input: jmp terminal_transfer_flush_input
terminal_upload_local_cancel: jmp terminal_transfer_local_cancel
terminal_upload_carrier: jmp terminal_transfer_carrier_present
terminal_upload_status: jmp terminal_transfer_status
terminal_upload_filename_display: jmp terminal_transfer_display_path
terminal_upload_unsupported: jmp terminal_transfer_unsupported
SEGMENT _DATA public class=DATA use16
terminal_upload_blocks_accepted: dw 0
GLOBAL terminal_upload_accepted_bytes,_terminal_upload_accepted_bytes
_terminal_upload_accepted_bytes:
terminal_upload_accepted_bytes: dd 0
