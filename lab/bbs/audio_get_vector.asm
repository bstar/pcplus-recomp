bits 16
cpu 8086
org 100h
mov ax,351ch
int 21h
mov [vector],bx
mov [vector+2],es
mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc fail
mov bx,ax
mov ah,40h
mov cx,4
mov dx,vector
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail:
mov ax,4c01h
int 21h
vector: dd 0
filename: db 'D:\KEYNEW.BIN',0
