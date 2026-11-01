; Owned DOS child: clear the real read-only bit and record before/after.
BITS 16
CPU 8086
ORG 100h
mov dx,path
mov ax,4300h
int 21h
jc failed
mov [sample+2],cx
and cx,0xfffe
mov ax,4301h
int 21h
jc failed
mov ax,4300h
int 21h
jc failed
mov [sample+4],cx
test cx,1
jnz failed
mov dx,filename
xor cx,cx
mov ah,3ch
int 21h
jc failed
mov bx,ax
mov cx,6
mov dx,sample
mov ah,40h
int 21h
jc .close_failed
cmp ax,6
jne .close_failed
mov ah,3eh
int 21h
jc failed
mov ax,4c00h
int 21h
.close_failed:
mov ah,3eh
int 21h
failed:
mov ax,4c01h
int 21h
path: db 'D:\PCPLUS.FON',0
filename: db 'D:\CLEAR.BIN',0
sample: dw 0x4143,0,0
