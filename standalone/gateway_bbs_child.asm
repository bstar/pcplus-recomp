; Owned test interpreter: record actual empty-tail EXEC, mark the passive
; observer, change video mode and wait with interrupts enabled. No UART I/O.
BITS 16
CPU 8086
ORG 100h
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,80h
 mov cx,2
 mov ah,40h
 int 21h
 jc failed
 cmp ax,2
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,0d741h
 mov bx,1
 int 2fh
 mov ax,13h
 int 10h
 xor ax,ax
 int 1ah
 mov si,dx
.wait:
 sti
 hlt
 xor ax,ax
 int 1ah
 sub dx,si
 cmp dx,18
 jb .wait
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
name: db 'D:\GWCHILD.BIN',0
