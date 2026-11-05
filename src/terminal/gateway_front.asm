BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
global terminal_gateway_key_far
extern _gateway_start
terminal_gateway_key_far:
 cmp ax,0x6b00
 jne .pass
 push ax
 call far _gateway_start
 pop ax
 stc
 retf
.pass:
 clc
 retf
global _gateway_clock_ready,_gateway_ticks,_gateway_notice
global _gateway_video_ready
_gateway_video_ready:
 push bx
 push bp
 push si
 push di
 push es
 mov ah,0x0f
 int 0x10
 cmp ax,0x5003
 jne .bad
 or bh,bh
 jne .bad
 mov ax,1
 jmp .done
.bad:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 pop bx
 retf
_gateway_clock_ready:
 in al,0x21
 test al,1
 mov ax,0
 jnz .done
 inc ax
.done:
 retf
_gateway_ticks:
 push es
 pushf
 cli
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 retf
extern connection_notice_resident
_gateway_notice:
 push bp
 mov bp,sp
 push si
 mov si,[bp+6]
 call far connection_notice_resident
 pop si
 pop bp
 retf
SEGMENT _TEXT public class=CODE use16
global _gateway_connection_poll
extern terminal_connection_poll
_gateway_connection_poll:
 call terminal_connection_poll
 retf
