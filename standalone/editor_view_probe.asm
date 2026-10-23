; Independent timer snapshot of the combined editor's selected last field.
BITS 16
CPU 8086
ORG 100h
jmp start
old1c: dw 0,0
magic: dw 0x5653
capture:
seen: dw 0
cursor: dw 0
screen: times 4000 db 0
capture_end:
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cmp word [cs:seen],0
 jne .done
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 cmp ah,18
 jne .done
 mov [cs:cursor],ax
 mov ax,0xb800
 mov es,ax
 cmp byte [es:18*160+4],'P'
 jne .done
 cmp byte [es:18*160+6],'r'
 jne .done
 cmp byte [es:19*160+4],'0'
 jne .done
 cmp byte [es:19*160+6],' '
 jne .done
 push cs
 pop es
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov di,screen
 mov cx,2000
 cld
 rep movsw
 mov word [cs:seen],1
.done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old1c]
start:
 cmp byte [0x80],0
 je collect
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 mov ax,0x351c
 int 0x21
 cmp bx,handler
 jne failed
 cmp word [es:magic],0x5653
 jne failed
 push ds
 push es
 lds dx,[es:old1c]
 mov ax,0x251c
 int 0x21
 pop es
 pop ds
 push es
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,capture
 mov cx,capture_end-capture
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,capture_end-capture
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'VIEW.BIN',0
resident_end:
