BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
%endmacro
%macro leave 0
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
%endmacro
global _line_kernel_attr,_line_kernel_open,_line_kernel_create
 global _line_kernel_read,_line_kernel_write,_line_kernel_close,_line_kernel_rename,_line_kernel_delete
_line_kernel_attr:
 enter
 mov dx,[bp+4]
 mov ax,4300h
 int 21h
 jc .done
 mov bx,[bp+6]
 mov [bx],cx
 xor ax,ax
.done:
 leave
_line_kernel_open:
 enter
 cmp word [bp+6],0
 jne .bad
 mov dx,[bp+4]
 mov ax,3da0h ; read only, deny writes, private descriptor
 int 21h
 jc .done
 mov bx,[bp+8]
 mov [bx],ax
 xor ax,ax
 jmp .done
.bad:
 mov ax,1
.done:
 leave
_line_kernel_create:
 enter
 mov dx,[bp+4]
 mov cx,[bp+6]
 mov ah,5bh
 int 21h
 jc .done
 mov bx,[bp+8]
 mov [bx],ax
 xor ax,ax
.done:
 leave
%macro io 2
_%1:
 enter
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ah,%2
 int 21h
 jc .done
 mov bx,[bp+10]
 mov [bx],ax
 xor ax,ax
.done:
 leave
%endmacro
io line_kernel_read,3fh
io line_kernel_write,40h
_line_kernel_close:
 enter
 mov bx,[bp+4]
 mov ah,3eh
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
_line_kernel_rename:
 enter
 push ds
 pop es
 mov dx,[bp+4]
 mov di,[bp+6]
 mov ah,56h
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
_line_kernel_delete:
 enter
 mov dx,[bp+4]
 mov ah,41h
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
