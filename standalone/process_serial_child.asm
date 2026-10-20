BITS 16
CPU 8086
ORG 0x100
%if CHILD_PORT=1
%define BASE 0x3f8
%define VECTOR 12
%define MASK 16
%else
%define BASE 0x2f8
%define VECTOR 11
%define MASK 8
%endif
mov dx,BASE+3
in al,dx
cmp al,3
jne failed
mov dx,BASE+1
in al,dx
or al,al
jnz failed
mov dx,BASE+4
in al,dx
test al,2
jnz failed
mov al,1 ;DTR retained; child controls RTS/OUT2 and leaves its own vector.
out dx,al
mov dx,BASE+3
mov al,0x9e
out dx,al
mov dx,BASE
mov al,0x34
out dx,al
inc dx
mov al,0x12
out dx,al
in al,0x21
xor al,0x20 ;Unrelated PIC bit must survive resume, then close restores baseline.
or al,MASK
out 0x21,al
mov ax,0x2500+VECTOR
mov dx,handler
int 0x21
mov dx,name
xor cx,cx
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,message
mov cx,4
mov ah,0x40
int 0x21
mov ah,0x3e
int 0x21
mov ax,0x4c25
int 0x21
failed: mov ax,0x4c63
int 0x21
handler: iret
name: db 'CHILD.OUT',0
message: db 'COM', '0'+CHILD_PORT
