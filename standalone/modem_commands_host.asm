; Source-only DOS command decoder self-check; no UART or private configuration.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
%macro push_value 1
 mov ax,%1
 push ax
%endmacro
extern modem_expand_bounded
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 push_value 130
 push_value 11
 push_value modem_destination
 push_value valid_command
 call modem_expand_bounded
 mov bx,sp
 lea sp,[bx+8]
 jc .failed
 cmp ax,5
 jne .failed
 cmp word [modem_destination],0x5441
 jne .failed
 cmp word [modem_destination+2],0xff0d
 jne .failed
 cmp word [modem_destination+4],0x005e
 jne .failed
 cmp word [modem_destination-2],0xa55a
 jne .failed
 cmp word [modem_destination+130],0x5aa5
 jne .failed
 push_value 130
 push_value 5
 push_value modem_destination
 push_value bad_command
 call modem_expand_bounded
 mov bx,sp
 lea sp,[bx+8]
 jnc .failed
 cmp ax,3
 jne .failed
 cmp word [modem_destination],0x5441
 jne .failed
 push_value 2
 push_value 11
 push_value modem_destination
 push_value valid_command
 call modem_expand_bounded
 mov bx,sp
 lea sp,[bx+8]
 jnc .failed
 cmp ax,4
 jne .failed
 cmp word [modem_destination],0x5441
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
valid_command: db 'AT^M^@^^^',0
bad_command: db 'BAD^',0
global modem_source,modem_destination
modem_source: times 129 db 0
dw 0xa55a
modem_destination: times 130 db 0x5a
dw 0x5aa5
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
