; Explicit synthetic UART/time/stat/UI fixture, not a live transfer engine.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern metadata_send_ymodem,metadata_parse_ymodem,metadata_end_ymodem
global _transfer_metadata_dos_test
_transfer_metadata_dos_test:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 push ds
 pop es
 cld
 mov word [metadata_protocol],5
 mov word [metadata_size_low],11521
 mov word [metadata_size_high],0
 mov word [fixture_carrier],1
 mov word [fixture_cancel],0
 mov word [fixture_wire_count],0
 mov word [fixture_script],6
 mov word [fixture_script_count],1
 mov word [fixture_script_index],0
 mov ax,fixture_filename
 push ax
 call metadata_send_ymodem
 add sp,2
 cmp ax,1
 jne .send_failed
 cmp word [fixture_wire_count],133
 jne .send_failed
 mov si,fixture_wire
 mov di,expected_header
 mov cx,133
 repe cmpsb
 jne .send_failed
 mov word [metadata_buffer_pointer],fixture_wire+3
 mov word [metadata_size_low],0
 mov word [metadata_size_high],0
 mov word [metadata_batch_end],0
 mov word [fixture_display_calls],0
 call metadata_parse_ymodem
 cmp word [metadata_size_low],11521
 jne .parse_failed
 cmp word [metadata_size_high],0
 jne .parse_failed
 cmp word [metadata_batch_end],0
 jne .parse_failed
 cmp word [fixture_display_calls],1
 jne .parse_failed
 push ds
 pop es
 mov si,metadata_filename
 mov di,expected_name
 mov cx,12
 repe cmpsb
 jne .parse_failed
 mov word [fixture_wire_count],0
 mov word [fixture_script],0x43
 mov word [fixture_script+2],6
 mov word [fixture_script_count],2
 mov word [fixture_script_index],0
 mov word [fixture_timeout_calls],0
 call metadata_end_ymodem
 cmp word [fixture_wire_count],133
 jne .end_failed
 cmp word [fixture_timeout_calls],2
 jne .end_failed
 cmp byte [fixture_wire],1
 jne .end_failed
 cmp byte [fixture_wire+1],0
 jne .end_failed
 cmp byte [fixture_wire+2],255
 jne .end_failed
 mov si,fixture_wire+3
 mov cx,130
.zero:
 cmp byte [si],0
 jne .end_failed
 inc si
 loop .zero
 ; Feed actual empty header payload through original parser as well.
 mov word [metadata_buffer_pointer],fixture_wire+3
 call metadata_parse_ymodem
 cmp word [metadata_batch_end],1
 jne .end_failed
 xor ax,ax
 jmp .return
.send_failed:
 mov ax,1
 jmp .return
.parse_failed:
 mov ax,2
 jmp .return
.end_failed:
 mov ax,3
.return:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

global metadata_transmit_byte,metadata_timed_byte,metadata_local_cancel
global metadata_carrier,metadata_stat_file,metadata_display_start,metadata_unwind
global receive_delay,receive_flush_input
metadata_transmit_byte:
 push bp
 mov bp,sp
 push bx
 mov bx,[fixture_wire_count]
 cmp bx,4096
 jae .overflow
 mov ax,[bp+4]
 mov [fixture_wire+bx],al
 inc word [fixture_wire_count]
 pop bx
 pop bp
 ret 2
.overflow:
 int3
 jmp .overflow
metadata_timed_byte:
 push bp
 mov bp,sp
 push bx
 inc word [fixture_timeout_calls]
 mov bx,[fixture_script_index]
 cmp bx,[fixture_script_count]
 jae .empty
 inc word [fixture_script_index]
 shl bx,1
 mov ax,[fixture_script+bx]
 jmp .done
.empty:
 mov ax,0xffff
.done:
 pop bx
 pop bp
 ret 2
metadata_local_cancel:
 mov ax,[fixture_cancel]
 ret
metadata_carrier:
 mov ax,[fixture_carrier]
 ret
metadata_stat_file:
 inc word [fixture_stat_calls]
 xor ax,ax
 ret
metadata_display_start:
 inc word [fixture_display_calls]
 ret
receive_delay:
 inc word [fixture_delay_calls]
 ret 2
receive_flush_input:
 inc word [fixture_flush_calls]
 mov word [receive_queued_count],0
 ret
metadata_unwind:
 int3
.halt:
 jmp .halt

SEGMENT _DATA public class=DATA use16
global metadata_protocol,metadata_buffer_pointer,metadata_size_low,metadata_size_high
global metadata_crc_high,metadata_crc_low,metadata_checkpoint,metadata_date,metadata_time
global metadata_filename,metadata_batch_end,metadata_identification,metadata_input
global fixture_wire,fixture_wire_count,fixture_script,fixture_script_index,fixture_script_count
global fixture_cancel,fixture_carrier,fixture_stat_calls,fixture_display_calls,fixture_timeout_calls
global fixture_filename,fixture_delay_calls,fixture_flush_calls,receive_queued_count
metadata_protocol dw 5
metadata_buffer_pointer dw metadata_input
metadata_size_low dw 0
metadata_size_high dw 0
metadata_crc_high dw 0
metadata_crc_low dw 0
metadata_checkpoint times 16 dw 0
metadata_date dw 0
metadata_time dw 0
metadata_batch_end dw 0
metadata_identification db 'PROCOMM PLUS    ',0
metadata_filename times 66 db 0
metadata_input times 1024 db 0
fixture_filename db 'LAB\PCXTEST.BIN',0
 times 64-($-fixture_filename) db 0
fixture_wire times 4096 db 0
fixture_wire_count dw 0
fixture_script times 64 dw 0
fixture_script_index dw 0
fixture_script_count dw 0
fixture_cancel dw 0
fixture_carrier dw 1
fixture_stat_calls dw 0
fixture_display_calls dw 0
fixture_timeout_calls dw 0
fixture_delay_calls dw 0
fixture_flush_calls dw 0
receive_queued_count dw 0
expected_name db 'PCXTEST.BIN',0
expected_header db 1,0,255,'PCXTEST.BIN',0,'11521',0
 times 131-($-expected_header) db 0
 db 0x4a,0x67 ; independent CCITT CRC of the 128-byte metadata payload
