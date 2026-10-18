; Diagnostic memory/UART boundary fixture, deliberately not a live transfer engine.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern receive_at_dc6a,receive_at_daea,receive_ack
GLOBAL _transfer_receive_probe,_transfer_receive_dos_test
_transfer_receive_probe:
 push bp
 mov bp,sp
 sub sp,0x18
 push bx
 push si
 push di
 mov ax,8
 mov bx,[bp+4]
 cmp bx,receive_input
 jne .return
 mov cx,[bp+6]
 jcxz .return
 cmp cx,1029
 ja .return
 mov dx,bx
 add dx,cx
 jc .return
 cmp word [bp+8],1
 ja .return
 mov ax,[bp+10]
 mov [receive_last_block],ax
 mov ax,[bp+8]
 mov di,ax
 mov ax,receive_payload
 mov [receive_buffer_pointer],ax
 xor ax,ax
 mov [receive_buffer_used],ax
 mov [receive_blocks_accepted],ax
 mov [receive_error_count],ax
 mov [receive_total_low],ax
 mov [receive_total_high],ax
 mov [receive_session_low],ax
 mov [receive_session_high],ax
 mov [receive_streaming_mode],ax
 mov [receive_wire_count],ax
 mov [receive_status_code],ax
 mov [receive_cancel_code],ax
 mov [receive_delay_calls],ax
 mov [receive_flush_calls],ax
 mov [receive_progress_calls],ax
 mov [bp-4],ax
 mov [bp-14h],ax
 mov [bp-0eh],ax
 mov word [bp-2],0xffff
 xor ax,ax
 mov al,[bx]
 mov [bp-10h],ax
 inc bx
 dec cx
 mov [receive_input_pointer],bx
 mov [receive_input_remaining],cx
 mov [receive_queued_count],cx
 jmp receive_at_dc6a
.return:
 pop di
 pop si
 pop bx
 mov sp,bp
 pop bp
 ret

global receive_validated,receive_buffer_full,receive_complete,receive_eot,receive_unsupported_control,receive_disk_commit
receive_validated:
 cmp word [bp-0eh],0
 jne .metadata
 jmp receive_at_daea
.metadata:
 mov ax,10
 jmp _transfer_receive_probe.return
receive_disk_commit:
 mov ax,13
 jmp _transfer_receive_probe.return
receive_buffer_full:
 mov ax,11
 jmp _transfer_receive_probe.return
receive_eot:
 mov ax,6
 jmp _transfer_receive_probe.return
receive_unsupported_control:
 mov ax,7
 jmp _transfer_receive_probe.return
receive_complete:
 cmp word [receive_cancel_code],7
 jne .not_cancel
 mov ax,15
 jmp _transfer_receive_probe.return
.not_cancel:
 xor ax,ax
 cmp word [receive_blocks_accepted],0
 jne .done
 inc ax
 cmp word [receive_status_code],0
 je .done
 cmp word [receive_status_code],1
 jne .not_control_timeout
 mov ax,14
 jmp .done
.not_control_timeout:
 mov ax,2
 cmp word [receive_status_code],8
 je .done
 inc ax
 cmp word [receive_status_code],7
 je .done
 inc ax
 cmp word [receive_status_code],2
 jne .done
 inc ax
.done:
 jmp _transfer_receive_probe.return

global receive_timed_byte,receive_header_byte,receive_flush_input,receive_status,receive_progress,receive_transmit_byte,receive_delay
receive_timed_byte:
 call receive_header_byte
 ret 2
receive_header_byte:
 cmp word [receive_input_remaining],0
 je .empty
 push bx
 mov bx,[receive_input_pointer]
 xor ax,ax
 mov al,[bx]
 inc word [receive_input_pointer]
 dec word [receive_input_remaining]
 dec word [receive_queued_count]
 pop bx
 ret
.empty:
 mov ax,0xffff
 ret
receive_flush_input:
 inc word [receive_flush_calls]
 mov word [receive_input_remaining],0
 mov word [receive_queued_count],0
 ret
receive_status:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [receive_status_code],ax
 pop bp
 ret
global receive_post_event
receive_post_event:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 mov [receive_cancel_code],ax
 pop bp
 ret
receive_progress:
 inc word [receive_progress_calls]
 ret
receive_delay:
 inc word [receive_delay_calls]
 ret 2
receive_transmit_byte:
 push bp
 mov bp,sp
 push bx
 mov bx,[receive_wire_count]
 cmp bx,128
 jae .full
 mov ax,[bp+4]
 mov [receive_wire+bx],al
 inc word [receive_wire_count]
.full:
 pop bx
 pop bp
 ret 2
_transfer_receive_dos_test:
 push bx
 push si
 push di
 mov ax,133
 call .probe
 or ax,ax
 jnz .fail
 cmp word [receive_blocks_accepted],1
 jne .fail
 cmp word [receive_buffer_used],128
 jne .fail
 cmp byte [receive_wire],6
 jne .fail
 mov byte [receive_input+132],1
 mov ax,133
 call .probe
 cmp ax,4
 jne .fail
 cmp word [receive_error_count],1
 jne .fail
 cmp byte [receive_wire],0x15
 jne .fail
 mov byte [receive_input+132],0
 mov word [receive_input+1],0xff00
 mov ax,133
 call .probe
 cmp ax,1
 jne .fail
 cmp word [receive_blocks_accepted],0
 jne .fail
 cmp byte [receive_wire],6
 jne .fail
 mov word [receive_input+1],0xfd01
 mov ax,133
 call .probe
 cmp ax,3
 jne .fail
 mov word [receive_input+1],0xfc03
 mov ax,133
 call .probe
 cmp ax,2
 jne .fail
 mov word [receive_input+1],0xfe01
 mov ax,17
 call .probe
 cmp ax,5
 jne .fail
 mov byte [receive_input],4
 mov ax,1
 call .probe
 cmp ax,6
 jne .fail
 cmp word [receive_wire_count],2
 jne .fail
 cmp word [receive_wire],0x0615
 jne .fail
 mov byte [receive_input],0x55
 mov word [receive_input+1],0x1818
 mov ax,3
 call .probe
 cmp ax,15
 jne .fail
 cmp word [receive_cancel_code],7
 jne .fail
 cmp word [receive_wire_count],0
 jne .fail
 xor ax,ax
 jmp .done
.fail:
 mov ax,1
.done:
 pop di
 pop si
 pop bx
 ret
.probe:
 xor cx,cx
 push cx
 mov bx,1
 push bx
 push ax
 mov ax,receive_input
 push ax
 call _transfer_receive_probe
 add sp,8
 ret
SEGMENT _DATA public class=DATA use16
global receive_input,receive_payload,receive_wire,receive_input_pointer,receive_input_remaining
receive_input: db 1,1,254
 times 1026 db 0
receive_payload: times 2048 db 0xcc
receive_wire: times 128 db 0xcc
receive_input_pointer: dw 0
receive_input_remaining: dw 0
global receive_block_size
receive_block_size: dw 0
global receive_blocks_accepted
receive_blocks_accepted: dw 0
global receive_buffer_pointer
receive_buffer_pointer: dw 0
global receive_buffer_used
receive_buffer_used: dw 0
global receive_crc_high
receive_crc_high: dw 0
global receive_crc_low
receive_crc_low: dw 0
global receive_delay_calls
receive_delay_calls: dw 0
global receive_error_count
receive_error_count: dw 0
global receive_flush_calls
receive_flush_calls: dw 0
global receive_last_block
receive_last_block: dw 0
global receive_progress_calls
receive_progress_calls: dw 0
global receive_protocol
receive_protocol: dw 0
global receive_queued_count
receive_queued_count: dw 0
global receive_session_high
receive_session_high: dw 0
global receive_session_low
receive_session_low: dw 0
global receive_status_code
receive_status_code: dw 0
global receive_streaming_mode
receive_streaming_mode: dw 0
global receive_total_high
receive_total_high: dw 0
global receive_total_low
receive_total_low: dw 0
global receive_wire_block
receive_wire_block: dw 0
global receive_wire_complement
receive_wire_complement: dw 0
global receive_wire_count
receive_wire_count: dw 0
global receive_wire_high
receive_wire_high: dw 0
global receive_wire_low
receive_wire_low: dw 0
global receive_event_queue,receive_cancel_code
receive_event_queue: dw 0
receive_cancel_code: dw 0
