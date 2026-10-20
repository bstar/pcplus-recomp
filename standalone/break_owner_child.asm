BITS 16
CPU 8086
ORG 0x100
 mov ax,0x351b
 int 0x21
 mov [observed],bx
 mov [observed+2],es
 mov ax,0x3523
 int 0x21
 mov [observed+4],bx
 mov [observed+6],es
 mov ax,0x3300
 int 0x21
 mov [observed+8],dl
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,observed
 mov cx,9
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,9
 jne failed
 mov ah,0x3e
 int 0x21
 ; Leave a stale child-owned INT1B and a changed global break setting.
 mov dx,handler
 mov ax,0x251b
 int 0x21
 mov al,0x23
 int 0x21
 mov ax,0x3301
 mov dl,1
 int 0x21
 mov ax,0x1234
 mov ds,ax
 mov ax,0x4c2a
 int 0x21
failed:
 mov ax,0x4c63
 int 0x21
handler: iret
name: db 'BRKWIT.BIN',0
observed: times 9 db 0
