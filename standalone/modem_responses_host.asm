; Actual DOS bounded decoder self-check with synthetic responses.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern modem_responses_reset_bounded,modem_responses_feed_bounded
extern modem_response_slots,modem_response_cursors
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov word [modem_response_slots],0x4b4f ; OK
 mov byte [modem_response_slots+2],0
 call modem_responses_reset_bounded
 jc .fail
 mov ax,'O'
 push ax
 call modem_responses_feed_bounded
 pop bx
 jc .fail
 cmp ax,0xffff
 jne .fail
 mov ax,'K'
 push ax
 call modem_responses_feed_bounded
 pop bx
 jc .fail
 or ax,ax
 jnz .fail
 mov word [modem_response_cursors],0xffff
 mov ax,'X'
 push ax
 call modem_responses_feed_bounded
 pop bx
 jnc .fail
 cmp ax,2
 jne .fail
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
