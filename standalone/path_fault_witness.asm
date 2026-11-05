; Bounded PROGRAM witness used by paired rollback/quarantine tests only.
BITS 16
CPU 8086
ORG 100h
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
jc failed
mov bx,ax
mov dx,message
mov cx,message_end-message
mov ah,40h
int 21h
jc failed
cmp ax,message_end-message
jne failed
mov ah,3eh
int 21h
jc failed
mov ax,4c00h
int 21h
failed:
mov ax,4c01h
int 21h
name: db 'D:\WITNESS.TXT',0
message: db 'PROGRAM accepted after verified rollback',13,10
message_end:
