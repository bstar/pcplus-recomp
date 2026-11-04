; Owned DOS test child: leave graphics13, append proof of real execution, exit.
BITS 16
CPU 8086
ORG 0x100
 mov ax,0x13
 int 0x10
 mov ax,0x3d02
 mov dx,leaf
 int 0x21
 jnc .opened
 mov ah,0x3c
 xor cx,cx
 mov dx,leaf
 int 0x21
 jc .failed
.opened:
 mov bx,ax
 mov ax,0x4202
 xor cx,cx
 xor dx,dx
 int 0x21
 jc .close_failed
 mov ah,0x40
 mov cx,1
 mov dx,proof
 int 0x21
 jc .close_failed
 cmp ax,1
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc .failed
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
leaf: db 'CHILD.LOG',0
proof: db 0x13
