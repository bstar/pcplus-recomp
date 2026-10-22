; Keep the emulator alive after the DOS application returns. Its null-modem
; backend batches host socket writes separately from guest UART TEMT. No UART
; access, terminal input or product state modification occurs here.
bits 16
cpu 8086
org 100h
push cs
pop ds
pushf
pop ax
test ax,0x200
jz bad
xor ah,ah
int 1ah
mov [sample],dx
mov [sample+2],cx
again:
xor ah,ah
int 1ah
mov ax,dx
mov dx,cx
sub ax,[sample]
sbb dx,[sample+2]
jnc normalized
add ax,0x00b0
adc dx,0x0018 ; BIOS midnight wrap:1573040 ticks per day.
normalized:
or dx,dx
jnz done
cmp ax,2
jb again
done:
mov [sample+4],ax
mov [sample+6],dx
mov dx,name
xor cx,cx
mov ah,0x3c
int 21h
jc bad
mov bx,ax
mov dx,sample
mov cx,8
mov ah,0x40
int 21h
jc close_bad
cmp ax,8
jne close_bad
mov ah,0x3e
int 21h
jc bad
mov ax,0x4c00
int 21h
close_bad:
mov ah,0x3e
int 21h
bad:
mov ax,0x4c01
int 21h
name: db 'DRAIN.BIN',0
sample: times 4 dw 0
