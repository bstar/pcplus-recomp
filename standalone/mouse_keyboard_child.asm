; Real DOS child verifies the parent's callback is absent, then changes driver state.
BITS 16
CPU 8086
ORG 0x100
start:
 push cs
 pop es
 xor cx,cx
 xor dx,dx
 mov ax,0x14
 int 0x33
 or cx,cx
 jnz failed
 mov ax,4
 mov cx,500
 mov dx,100
 int 0x33
 mov ax,0x1a
 mov bx,50
 mov cx,60
 mov dx,70
 int 0x33
 push cs
 pop es
 mov dx,callback
 mov cx,0x0b
 mov ax,0x0c
 int 0x33
 ; Independently read back and retire this child's actual callback.
 push cs
 pop es
 xor cx,cx
 xor dx,dx
 mov ax,0x14
 int 0x33
 cmp cx,0x0b
 jne failed
 mov ax,cs
 mov bx,es
 cmp ax,bx
 jne failed
 cmp dx,callback
 jne failed
 mov dx,marker
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,message
 mov cx,message_end-message
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,message_end-message
 jne failed
 mov ah,0x3e
 int 0x21
%ifdef CHANGE_VECTOR
 push ds
 xor ax,ax
 mov ds,ax
 xor dx,dx
 mov ax,0x2533
 int 0x21
 pop ds
%endif
 mov ax,0x4c25
 int 0x21
callback: retf
failed:
 mov ax,0x4c63
 int 0x21
marker: db 'CHILD.OK',0
message: db 'MOUSE CHILD',13,10
message_end:
