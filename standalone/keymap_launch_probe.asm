; Owned DOS fixture: record successful PROGRAM entry, then return normally.
; This is not the mapper and must never be included in an application package.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global start
start:
 push cs
 pop ds
 mov dx,path
 mov ax,0x3d01
 int 0x21
 jnc .opened
 cmp ax,2
 jne .failed
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .failed
.opened:
 mov bx,ax
 xor cx,cx
 xor dx,dx
 mov ax,0x4202
 int 0x21
 jc .failed
 mov dx,marker
 mov cx,1
 mov ah,0x40
 int 0x21
 jc .failed
 cmp ax,1
 jne .failed
 mov ah,0x3e
 int 0x21
 jc .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c07
 int 0x21
path: db 'D:\LAUNCH.LOG',0
marker: db 'K'
SEGMENT STACK stack class=STACK use16
resb 256
