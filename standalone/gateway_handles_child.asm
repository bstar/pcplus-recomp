BITS 16
CPU 8086
ORG 0x100
 xor ax,ax
 mov al,[0x82]
 sub al,'0'
 mov bx,ax
 mov si,report
 call inherited
 cmp byte [0x84],'-'
 je .own
 xor ax,ax
 mov al,[0x84]
 sub al,'0'
 mov bx,ax
 add si,4
 call inherited
.own:
 mov ah,0x3c
 xor cx,cx
 mov dx,own_name
 int 0x21
 jc failed
 mov [report+8],ax
 mov bx,ax
 mov ah,0x40
 mov cx,1
 mov dx,own_byte
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
 mov ah,0x40
 mov cx,10
 mov dx,report
 int 0x21
 jc failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c25
 int 0x21
inherited:
 mov ah,0x40
 mov cx,1
 mov dx,foreign_byte
 int 0x21
 mov [si],ax
 mov ah,0x3e
 int 0x21
 jc .closed
 xor ax,ax
.closed:
 mov [si+2],ax
 ret
failed:
 mov ax,0x4c01
 int 0x21
own_name: db 'OWN.DAT',0
report_name: db 'CHILD.BIN',0
own_byte: db 'Y'
foreign_byte: db 'X'
report: times 5 dw 0
