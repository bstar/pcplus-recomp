; Maintained pure classification of overlay5:eA39..eAe7 observed actions.
; Near C(index,current_baud_index,autobaud) caller cleanup6.
; CF0 AXffffpending/0failure/1connected; DXeffectivebaud; BXbaud-change0/1.
; CF1 AX1invalidindex/2invalidbool/3invalidbaud. No UART/baud setter sideeffects.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global modem_response_classify
modem_response_classify:
 push bp
 mov bp,sp
 mov dx,[bp+6]
 cmp dx,8
 ja .bad_baud
 cmp word [bp+8],1
 ja .bad_bool
 xor bx,bx
 mov ax,[bp+4]
 cmp ax,0xffff
 je .success
 cmp ax,10
 ja .bad_index
 cmp ax,6
 ja .failure
 cmp word [bp+8],0
 je .connected
 cmp ax,dx
 je .connected
 mov dx,ax
 inc bx
.connected:
 mov ax,1
 jmp .success
.failure:
 xor ax,ax
.success:
 clc
 pop bp
 ret
.bad_index:
 mov ax,1
 jmp .error
.bad_bool:
 mov ax,2
 jmp .error
.bad_baud:
 mov ax,3
.error:
 stc
 pop bp
 ret
