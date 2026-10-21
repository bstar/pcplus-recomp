; Owned socket-close probe. Receive a declared count through actual UART I/O,
; write a witness, and let the normal DOSBox EXIT path close its TCP endpoint.
bits 16
cpu 8086
org 100h
%ifndef READ_COUNT
%define READ_COUNT 256
%endif
mov dx,3f9h
xor al,al
out dx,al
mov dx,3fbh
mov al,80h
out dx,al
mov dx,3f8h
mov al,12
out dx,al
inc dx
xor al,al
out dx,al
mov dx,3fbh
mov al,3
out dx,al
mov dx,3fch
out dx,al
mov bl,'R'
call send
mov cx,READ_COUNT
.receive:
mov dx,3fdh
.wait:
in al,dx
test al,1
jz .wait
mov dx,3f8h
in al,dx
mov [witness+2],al
inc word [witness]
loop .receive
mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc fail
mov bx,ax
mov ah,40h
mov cx,3
mov dx,witness
int 21h
cmp ax,3
jne fail
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail: mov ax,4c01h
int 21h
send:
mov dx,3fdh
.ready:
in al,dx
test al,20h
jz .ready
mov dx,3f8h
mov al,bl
out dx,al
ret
witness: dw 0
db 0
filename: db 'COUNT.BIN',0
