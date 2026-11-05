; Collect and retire the independent observer before writing its report.

bits 16
cpu 8086
org 100h
 mov ax,0xd7c2
 mov bx,0x4c43
 int 0x2f
 cmp ax,0xc51b
 jne fail
 cmp word [es:di],0xc51b
 jne fail
 mov [tsr],es
 mov si,di
 push ds
 push es
 pop ds
 pop es
 mov di,buffer
 mov cx,8212
 cld
 rep movsb
 push es
 pop ds
 cmp word [buffer+4],1024
 ja fail
 mov ax,0x3521
 int 0x21
 mov ax,es
 cmp ax,[tsr]
 jne fail
 cmp bx,[buffer+16]
 jne fail
 or word [verified],1
 mov ax,0x352f
 int 0x21
 mov ax,es
 cmp ax,[tsr]
 jne fail
 cmp bx,[buffer+18]
 jne fail
 or word [verified],2
 push ds
 mov dx,[buffer+8]
 mov ax,[buffer+10]
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 push ds
 mov dx,[buffer+12]
 mov ax,[buffer+14]
 mov ds,ax
 mov ax,0x252f
 int 0x21
 pop ds
 mov ax,0x3521
 int 0x21
 mov ax,es
 cmp ax,[buffer+10]
 jne fail
 cmp bx,[buffer+8]
 jne fail
 or word [verified],4
 mov ax,0x352f
 int 0x21
 mov ax,es
 cmp ax,[buffer+14]
 jne fail
 cmp bx,[buffer+12]
 jne fail
 or word [verified],8
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc fail
 mov bx,ax
 mov dx,report
 mov cx,8218
 mov ah,0x40
 int 0x21
 jc fail
 cmp ax,8218
 jne fail
 mov ah,0x3e
 int 0x21
 jc fail
 mov ax,0x4c00
 int 0x21
fail:
 mov ax,0x4c01
 int 0x21
tsr dw 0
filename db 'TRACE.BIN',0
report db 'GS21'
verified dw 0
buffer times 8212 db 0
