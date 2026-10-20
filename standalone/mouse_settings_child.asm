; Controlled editor replacement for invalid/failed-child acceptance cases.
BITS 16
CPU 8086
ORG 100h
 push cs
 pop ds
 mov dx,path
 mov ax,0x3d02
 int 0x21
 jc failed
 mov bx,ax
 mov ax,0x4200
 xor cx,cx
 mov dx,0x4e4
 int 0x21
 jc failed
 mov dx,scales
 mov cx,4
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,4
 jne failed
 mov ax,0x4200
 xor cx,cx
 mov dx,0x1ae
 int 0x21
 jc failed
 mov dx,color
 mov cx,2
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,2
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
%ifdef EXIT_FAILURE
 mov ax,0x4c09
%else
 mov ax,0x4c00
%endif
 int 0x21
failed:
 mov ax,0x4c0a
 int 0x21
path: db 'TEST.PRM',0
%ifdef EXIT_FAILURE
scales: dw 16,8
%else
scales: dw 0,8
%endif
color: dw 30
