; Explicit reset-boundary observer, not a production reset implementation.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
global width_request_invoke,terminal_reset_native
extern modes_width_request_native
..start:
 mov ax,DGROUP
 mov ds,ax
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne failed
 mov word [reset_configured_wide],0x7777
 mov word [width_request_argument],1
 call width_request_invoke
 cmp word [reset_configured_wide],0x7777
 jne failed
 cmp word [width_observed_configuration],1
 jne failed
 cmp word [width_observed_mode],0
 jne failed
 cmp word [width_reset_calls],1
 jne failed
 mov word [width_request_argument],0
 call width_request_invoke
 cmp word [reset_configured_wide],0x7777
 jne failed
 cmp word [width_observed_configuration],0
 jne failed
 cmp word [width_reset_calls],2
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
width_request_invoke:
 push word [width_request_argument]
 call modes_width_request_native
 ret
terminal_reset_native:
 push bp
 mov bp,sp
 inc word [width_reset_calls]
 mov ax,[reset_configured_wide]
 mov [width_observed_configuration],ax
 mov ax,[bp+4]
 mov [width_observed_mode],ax
 mov ax,[width_reset_replacement]
 mov [reset_configured_wide],ax
 mov ax,0xaaaa
 mov bx,0xbbbb
 mov cx,0xcccc
 mov dx,0xdddd
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
global reset_configured_wide,width_request_argument,width_observed_configuration
global width_observed_mode,width_reset_calls,width_reset_replacement
reset_configured_wide: dw 0
width_request_argument: dw 0
width_observed_configuration: dw 0
width_observed_mode: dw 0
width_reset_calls: dw 0
width_reset_replacement: dw 0x9999
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
resb 2048
global terminal_stack_top
terminal_stack_top:
