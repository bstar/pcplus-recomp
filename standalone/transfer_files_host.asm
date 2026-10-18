; Source-owned diagnostic startup and bounded synthetic FILE objects.
BITS 16
CPU 8086
GROUP DGROUP _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern files_fwrite,files_fflush,files_fclose,files_at_db2a,files_at_de20
global start,files_initialize,files_probe_periodic,files_probe_tail
start:
 mov ax,DGROUP
 mov ds,ax
 mov ss,ax
 mov sp,files_stack_top
 cmp byte [es:0x80],2
 jb .mode_ready
 mov al,[es:0x82]
 cmp al,'T'
 jne .not_text
 mov word [dos_text],1
 mov word [dos_expected_size],603
.not_text:
 cmp al,'U'
 jne .not_unbuffered
 mov word [dos_buffered],0
.not_unbuffered:
 cmp al,'F'
 jne .mode_ready
 mov byte [dos_closed_handle],1
 mov word [dos_buffered],0
.mode_ready:
 mov ax,0x3000
 int 0x21
 mov [program_dos_major],al
 ; Binary borrowed-buffer CRT path: write600 bytes, flush and close real DOS.
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov [saved_handle],ax
 mov bx,files_source
 xor cx,cx
.fill:
 mov [bx],cl
 inc bx
 inc cx
 cmp cx,600
 jb .fill
 push word [dos_text]
 push word [dos_buffered]
 push ax
 call files_initialize
 add sp,6
 or ax,ax
 jnz failed
 cmp byte [dos_closed_handle],0
 je .write
 mov bx,[saved_handle]
 mov ah,0x3e
 int 0x21
 jc failed
.write:
 mov ax,files_stream_table
 push ax
 mov ax,600
 push ax
 mov ax,1
 push ax
 mov ax,files_source
 push ax
 call files_fwrite
 add sp,8
 cmp byte [dos_closed_handle],0
 je .normal_write
 or ax,ax
 jnz failed
 mov ax,files_stream_table
 push ax
 call files_fclose
 add sp,2
 cmp ax,0xffff
 jne failed
 cmp byte [program_dos_error],6
 jne failed
 jmp success
.normal_write:
 cmp ax,600
 jne failed
 mov ax,files_stream_table
 push ax
 call files_fflush
 add sp,2
 or ax,ax
 jnz failed
 mov ax,files_stream_table
 push ax
 call files_fclose
 add sp,2
 or ax,ax
 jnz failed
 ; Re-open and verify exact bytes and EOF through actual DOS, outside CRT.
 mov dx,filename
 mov ax,0x3d00
 int 0x21
 jc failed
 mov bx,ax
 mov dx,files_capture
 mov cx,[dos_expected_size]
 inc cx
 mov ah,0x3f
 int 0x21
 jc failed
 cmp ax,[dos_expected_size]
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov si,files_source
 mov di,files_capture
 mov cx,600
 push ds
 pop es
 cld
 .verify:
 lodsb
 cmp word [dos_text],0
 je .compare
 cmp al,10
 jne .compare
 cmp byte [di],13
 jne failed
 inc di
.compare:
 cmp [di],al
 jne failed
 inc di
 loop .verify
success:
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21

; Near cdecl(handle,borrowed_buffer,text_mode), caller6, no IO.
; Only synthetic stream table entry0, fixed512-byte borrowed arena.
files_initialize:
 push bp
 mov bp,sp
 push si
 push di
 push bx
 push es
 cmp word [bp+4],20
 jae .invalid
 cmp word [bp+6],1
 ja .invalid
 cmp word [bp+8],1
 ja .invalid
 push ds
 pop es
 mov di,files_stream_table
 mov cx,160
 xor ax,ax
 cld
 rep stosw
 mov ax,files_buffer
 mov [files_stream_table],ax
 mov [files_stream_table+4],ax
 mov byte [files_stream_table+6],6
 mov word [files_extra_table+2],1
 cmp word [bp+6],0
 je .unbuffered
 mov byte [files_stream_table+6],2
 mov word [files_stream_table+2],512
 mov word [files_extra_table+2],512
 mov byte [files_extra_table],1
.unbuffered:
 mov ax,[bp+4]
 mov [files_stream_table+7],al
 mov bx,ax
 mov byte [files_handle_flags+bx],0
 cmp word [bp+8],0
 je .binary
 mov byte [files_handle_flags+bx],0x80
.binary:
 mov word [files_handle_limit],20
 mov word [files_overlay_cookie],0
 mov word [files_receive_flow_switch],0
 mov word [program_errno],0
 mov byte [program_dos_error],0
 mov word [files_status_code],0
 mov ax,files_source
 mov [files_receive_buffer],ax
 mov ax,files_stream_table
 mov [files_receive_stream],ax
 mov word [files_receive_used],600
 mov word [files_receive_size_low],0
 mov word [files_receive_size_high],0
 xor ax,ax
 jmp .initialized
.invalid:
 mov ax,1
.initialized:
 pop es
 pop bx
 pop di
 pop si
 pop bp
 ret

files_probe_periodic:
 push bp
 mov bp,sp
 sub sp,0x58
 push si
 push di
 jmp files_at_db2a
files_probe_tail:
 push bp
 mov bp,sp
 sub sp,0x58
 push si
 push di
 jmp files_at_de20

global files_receive_success,files_receive_resume,files_receive_failure,files_receive_stack_failure
files_receive_success:
files_receive_resume:
 mov ax,1
 jmp files_probe_done
files_receive_stack_failure:
 add sp,2
files_receive_failure:
 xor ax,ax
files_probe_done:
 pop di
 pop si
 mov sp,bp
 pop bp
 ret

global files_receive_status
files_receive_status:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [files_status_code],ax
 pop bp
 ret

SEGMENT _DATA public class=DATA use16
filename: db 'OWNED.BIN',0
saved_handle: dw 0
dos_text: dw 0
dos_buffered: dw 1
dos_expected_size: dw 600
dos_closed_handle: db 0
global files_source,files_buffer,files_capture,files_status_code
files_source: times 4096 db 0
files_buffer: times 512 db 0
files_capture: times 4096 db 0
files_status_code: dw 0
global files_stream_table,files_extra_table,files_extra_temporary,files_stdout,files_stderr,files_aux
files_stream_table: times 160 db 0
files_stdout equ files_stream_table+8
files_stderr equ files_stream_table+16
files_aux equ files_stream_table+32
files_extra_table: times 160 db 0
files_extra_temporary equ files_extra_table+4
global files_handle_limit,files_handle_flags
files_handle_limit: dw 20
files_handle_flags: times 32 db 0
global files_stack_floor,files_overlay_cookie,files_overlay_callback
files_stack_floor: dw files_stack_bottom
files_overlay_cookie: dw 0
files_overlay_callback: dw 0
global files_temp_prefix,files_temp_separator
files_temp_prefix: db 0
files_temp_separator: db 0
global files_receive_buffer,files_receive_stream,files_receive_used,files_receive_size_low,files_receive_size_high,files_receive_total_low,files_receive_total_high,files_receive_flow_switch
files_receive_buffer: dw 0
files_receive_stream: dw 0
files_receive_used: dw 0
files_receive_size_low: dw 0
files_receive_size_high: dw 0
files_receive_total_low: dw 0
files_receive_total_high: dw 0
files_receive_flow_switch: dw 0
global program_dos_major,program_errno,program_dos_error
program_dos_major: db 3
program_errno: dw 0
program_dos_error: db 0
SEGMENT STACK stack class=STACK use16
files_stack_bottom:
 times 8192 db 0
files_stack_top:
