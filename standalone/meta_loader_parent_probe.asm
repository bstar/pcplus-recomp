BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
global _meta_probe_write
; Near cdecl: far bytes, length. Return actual DOS error/short-write5 or zero.
_meta_probe_write:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push ds
 mov dx,[bp+4]
 mov ds,[bp+6]
 mov cx,[bp+8]
 mov bx,1
 mov ah,40h
 int 21h
 jc .done
 cmp ax,[bp+8]
 mov ax,5
 jne .done
 xor ax,ax
.done:
 pop ds
 pop dx
 pop cx
 pop bx
 pop bp
 ret
