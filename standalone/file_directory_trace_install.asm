; Passive DOS entry trace; AX/BX/CX/DS only, no DOS calls in handler.

bits 16
cpu 8086
org 100h
jmp install
old21 dd 0
old2f dd 0
state:
 dw 0xc51b,1,0,0
saved21 dd 0
saved2f dd 0
 dw hook21,hook2f
records times 8192 db 0
hook21:
 pushf
 cmp ah,0x4e
 je .record
 cmp ah,0x4f
 je .record
 cmp ah,0x1a
 je .record
 cmp ah,0x2f
 je .record
 cmp ax,0x4b00
 je .record
 cmp ah,0x40
 jne .not_write
 cmp cx,1
 je .chain
 jmp .record
.not_write:
 cmp ah,0x3e
 jne .chain
.record:
 push bp
 mov bp,sp
 push ax
 push bx
 push cx
 push dx
 push di
 push es
 mov di,[cs:state+4]
 cmp di,1024
 jb .space
 mov word [cs:state+6],1
 jmp .done
.space:
 shl di,1
 shl di,1
 shl di,1
 mov ax,[ss:bp-2]
 mov [cs:records+di],ax
 mov ax,[ss:bp-4]
 mov [cs:records+di+2],ax
 mov ax,[ss:bp-6]
 mov [cs:records+di+4],ax
 mov ax,ds
 mov [cs:records+di+6],ax
 inc word [cs:state+4]
.done:
 pop es
 pop di
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
.chain:
 popf
 jmp far [cs:old21]
hook2f:
 pushf
 cmp ax,0xd7c2
 jne .chain
 cmp bx,0x4c43
 jne .chain
 popf
 mov ax,0xc51b
 push cs
 pop es
 mov di,state
 iret
.chain:
 popf
 jmp far [cs:old2f]
install:
 mov ax,0xd7c2
 mov bx,0x4c43
 int 0x2f
 cmp ax,0xc51b
 je .fail
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [saved21],bx
 mov [old21+2],es
 mov [saved21+2],es
 mov ax,0x352f
 int 0x21
 mov [old2f],bx
 mov [saved2f],bx
 mov [old2f+2],es
 mov [saved2f+2],es
 mov dx,hook21
 mov ax,0x2521
 int 0x21
 mov dx,hook2f
 mov ax,0x252f
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
resident_end:
