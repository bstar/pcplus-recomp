; Empty-tail synthetic COMSPEC. Probe all possible private descriptor slots.
BITS 16
CPU 8086
ORG 0x100
%ifdef GATEWAY_UART_CHILD
%include "gateway_uart_child.inc"
%endif
 mov bx,5
 mov si,report
.next:
 mov cx,1
 mov dx,foreign_byte
 mov ah,0x40
 int 0x21
 mov [si],ax
 mov ah,0x3e
 int 0x21
 jc .closed
 xor ax,ax
.closed:
 mov [si+2],ax
 add si,4
 inc bx
 cmp bx,20
 jb .next
 mov ax,[0x80]
 mov [report+62],ax
 mov ah,0x3c
 xor cx,cx
 mov dx,own_name
 int 0x21
 jc failed
 mov [report+60],ax
 mov bx,ax
 mov cx,1
 mov dx,own_byte
 mov ah,0x40
 int 0x21
 jc failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ah,0x3c
 xor cx,cx
 mov dx,report_name
 int 0x21
 jc failed
 mov bx,ax
 mov cx,64
 mov dx,report
 mov ah,0x40
 int 0x21
 jc failed
 mov ah,0x3e
 int 0x21
 jc failed
%ifdef CHANGE_CWD
 mov dx,target
 mov ah,0x3b
 int 0x21
 jc failed
%endif
 mov ax,0x4c25
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
own_name: db 'D:\OWN.DAT',0
report_name: db 'D:\CHILD.BIN',0
target: db 'D:\TARGET',0
foreign_byte: db 'X'
own_byte: db 'Y'
report: times 64 db 0
