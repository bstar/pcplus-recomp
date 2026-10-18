; Scheduled peer UART with real maintained DOS storage callbacks. Reuse the
; explicit peer fixture without editing its original memory-file diagnostic.
%define composite_file_open composite_fixture_file_open
%define composite_file_write composite_fixture_file_write
%define composite_file_close composite_fixture_file_close
%define composite_io_reset composite_fixture_io_reset
%define composite_test_filename composite_fixture_test_filename
%include "transfer_session_composite_io.asm"
%undef composite_file_open
%undef composite_file_write
%undef composite_file_close
%undef composite_io_reset
%undef composite_test_filename
SEGMENT _TEXT
extern _transfer_native_open,_transfer_native_write,_transfer_native_close
extern _transfer_storage_begin
global composite_file_open,composite_file_write,composite_file_close
composite_file_open: jmp _transfer_native_open
composite_file_write: jmp _transfer_native_write
composite_file_close: jmp _transfer_native_close
global composite_io_reset
composite_io_reset:
 call composite_fixture_io_reset
 call _transfer_storage_begin
 ret

global _transfer_storage_prepare,_transfer_storage_owner_result
_transfer_storage_owner_result:
 mov ax,[composite_owner_result]
 ret
_transfer_storage_prepare:
 push bp
 push bx
 push si
 push di
 push es
 call composite_prepare_dos
 push ds
 pop es
 mov si,composite_schedule
 mov di,composite_input_data
 mov word [composite_schedule_count],13
 mov bx,1
.frame:
 mov word [si],6
 cmp bx,1
 jne .trigger_ready
 mov word [si],0x15
.trigger_ready:
 mov [si+2],di
 mov word [si+4],1028
 add si,6
 mov al,2
 stosb
 mov al,bl
 stosb
 not al
 stosb
 ; Each1024-byte block contains all256 values four times, shifted by17*block.
 mov ax,bx
 mov cl,4
 shl ax,cl
 add ax,bx
 mov cx,1024
.payload:
 stosb
 inc al
 loop .payload
 xor ax,ax
 stosb ; checksum of four complete byte cycles is0
 inc bx
 cmp bx,12
 jb .frame
 mov word [si],6
 mov [si+2],di
 mov word [si+4],1
 add si,6
 mov al,4
 stosb
 mov word [si],0x15
 mov [si+2],di
 mov word [si+4],1
 stosb
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
SEGMENT _DATA
global composite_test_filename
composite_test_filename: db 'PART.TMP',0
SEGMENT _TEXT
global _transfer_storage_control
_transfer_storage_control:
 push bp
 mov bp,sp
 cmp word [bp+4],'M'
 jne .not_mixed
 call storage_prepare_mixed
 jmp .done
.not_mixed:
 cmp word [bp+4],'T'
 jne .not_timeout
 mov word [composite_schedule_count],0
 jmp .done
.not_timeout:
 cmp word [bp+4],'X'
 jne .done
 ; Release actual doubleCAN only after first block's ACK.
 mov word [composite_schedule_count],2
 mov word [composite_schedule+6+4],2
 mov word [composite_input_data+1028],0x1818
.done:
 pop bp
 ret

; Legal mixed-size boundary:10112 bytes buffered then a1024-byte block.
; The native10240-byte flush threshold is checked only AFTER copying that block.
storage_prepare_mixed:
 push bp
 push bx
 push si
 push di
 push es
 push ds
 pop es
 mov si,composite_schedule
 mov di,composite_input_data
 mov word [composite_schedule_count],82
 mov bx,1
.frame:
 mov word [si],6
 cmp bx,1
 jne .trigger_ready
 mov word [si],0x15
.trigger_ready:
 mov [si+2],di
 mov bp,128
 mov al,1
 cmp bx,80
 jne .size_ready
 mov bp,1024
 inc al
.size_ready:
 mov cx,bp
 add cx,4
 mov [si+4],cx
 add si,6
 stosb
 mov al,bl
 stosb
 not al
 stosb
 mov ax,bx
 mov cl,4
 shl ax,cl
 add ax,bx
 mov cx,bp
 xor dx,dx
.payload:
 stosb
 add dl,al
 inc al
 loop .payload
 mov al,dl
 stosb
 inc bx
 cmp bx,81
 jb .frame
 mov word [si],6
 mov [si+2],di
 mov word [si+4],1
 add si,6
 mov al,4
 stosb
 mov word [si],0x15
 mov [si+2],di
 mov word [si+4],1
 stosb
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
