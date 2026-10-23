; Source-built real DOS child: observable file output and ordinary exit0.
BITS 16
CPU 8086
ORG 0x100
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,message
 mov cx,2
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,2
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c63
 int 0x21
filename: db 'SUCCESS.OK',0
message: db 'OK'
