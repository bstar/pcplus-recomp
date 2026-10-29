; Test-only DOS3+ allocation-strategy sample; never changes the strategy.
BITS 16
CPU 8086
ORG 100h
 mov ax,5800h
 int 21h
 jc failed
 mov [value],ax
 mov dx,before
 cmp byte [82h],'A'
 jne create
 mov dx,after
create:
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,value
 mov cx,2
 mov ah,40h
 int 21h
 jc failed
 cmp ax,2
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
value: dw 0
before: db 'C:\STRATB.BIN',0
after: db 'C:\STRATA.BIN',0
