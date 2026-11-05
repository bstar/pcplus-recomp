BITS 16
CPU 8086
ORG 100h
jmp start
old: dw 0,0
last: dw 0
stable: dw 0
prior: dw 0xffff
cursor: dw 0
shape: dw 0
sample: dw 0x4544,0,0
frames: times 28028 db 0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 inc word [sample+4]
 cmp word [sample+2],7
 jae .done
 mov ax,0x40
 mov es,ax
 mov ax,[es:50h]
 mov [cursor],ax
 mov ax,[es:60h]
 mov [shape],ax
 mov ax,0xb800
 mov es,ax
 cmp word [sample+4],70
 jb .done
.candidate:
 xor dx,dx
 xor si,si
 mov cx,2000
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 add dx,[cursor]
 add dx,[shape]
 cmp dx,[last]
 je .same
 mov [last],dx
 mov word [stable],0
 jmp .done
.same:
 inc word [stable]
 cmp word [stable],2
 jb .done
 cmp dx,[prior]
 je .done
 mov [prior],dx
 mov ax,[sample+2]
 mov bx,4004
 mul bx
 mov di,frames
 add di,ax
 inc word [sample+2]
 mov ax,[cursor]
 mov [di],ax
 mov ax,[shape]
 mov [di+2],ax
 add di,4
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
.done:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old]
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],4544h
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,28034
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old]
 mov ax,[es:old+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,28034
 mov ah,40h
 int 21h
 jc failed
 mov ah,3eh
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'C:\EDITVIEW.BIN',0
buffer: times 28034 db 0
