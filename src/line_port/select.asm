; Relocatable far-cdecl adapter around the exact native selector.
; Recording callbacks express native service requests; they NEVER touch UART.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT LINE_PORT_CODE public align=16 class=FARCODE use16
extern line_port_key
global _line_port_select
_line_port_select:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 push ds
 pop es
 cld
 mov si,[bp+6]
 mov di,line_port_port
 mov cx,5
 rep movsw
 mov word [native_events],0
 push word [bp+8]
 call line_port_key
 add sp,2
 mov si,line_port_port
 mov di,[bp+6]
 mov cx,5
 rep movsw
 mov ax,[native_events]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 retf

global line_port_bell,line_port_quiesce
line_port_bell:
 or word [native_events],1
 ret
line_port_quiesce:
 or word [native_events],2
 ret
SEGMENT _DATA public class=DATA use16
global line_port_port,line_port_baud,line_port_parity,line_port_stop,line_port_bits
line_port_port: dw 0
line_port_baud: dw 0
line_port_parity: dw 0
line_port_stop: dw 0
line_port_bits: dw 0
native_events: dw 0
