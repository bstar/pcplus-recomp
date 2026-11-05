; Owned COMSPEC fixture: records exact command-tail prefix and exits37.
BITS 16
CPU 8086
ORG 100h
%ifdef GATEWAY_CHANGE_CWD
mov dx,target
mov ah,3bh
int 21h
jc failed
%endif
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
mov ax,4c25h
int 21h
failed:
mov ax,4c63h
int 21h
name: db 'D:\GWSHELL.BIN',0
%ifdef GATEWAY_CHANGE_CWD
target: db 'D:\TARGET',0
%endif
