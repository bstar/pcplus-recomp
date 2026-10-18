; Maintained signed 16-bit decimal formatter for recovered report calls.
; csi_report_decimal(value,near_buffer,base): caller cleanup, returns near_buffer.
; Base10 only; buffer needs7 bytes. DS=SS. Preserves BP/SI/DI, flags volatile.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global csi_report_decimal
csi_report_decimal:
 push bp
 mov bp,sp
 push si
 push di
 mov di,[bp+6]
 mov si,di
 cmp word [bp+8],10
 jne .unsupported
 mov ax,[bp+4]
 test ax,0x8000
 jz .positive
 mov byte [di],'-'
 inc di
 neg ax
.positive:
 mov bx,10
 xor cx,cx
.digit:
 xor dx,dx
 div bx
 push dx
 inc cx
 or ax,ax
 jnz .digit
.write:
 pop ax
 add al,'0'
 mov [di],al
 inc di
 loop .write
 mov byte [di],0
 mov ax,si
 pop di
 pop si
 pop bp
 ret
.unsupported:
 mov byte [di],0
 mov ax,si
 pop di
 pop si
 pop bp
 ret
