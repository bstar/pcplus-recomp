BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _retained_input_emit
_retained_input_emit:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push ds
 push es
 pushf
 mov bx,0x40
 mov ds,bx
 mov ax,2
 xor si,si
 xor di,di
 cli
 call far [ss:bp+4]
 mov bx,ds
 mov ax,1
 cmp bx,0x40
 je .done
 xor ax,ax
.done:
 popf
 pop es
 pop ds
 pop di
 pop si
 pop bx
 pop bp
 ret
