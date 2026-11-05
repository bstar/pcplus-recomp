; Source-only DOS3+ read-only viewer boundary. Near cdecl within FILE_CODE.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
global _viewer_kernel_canonical,_viewer_kernel_attributes,_viewer_kernel_open
global _viewer_kernel_device,_viewer_kernel_read,_viewer_kernel_seek,_viewer_kernel_close
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
%endmacro
%macro leave 0
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
%endmacro
_viewer_kernel_canonical:
 enter
 push ds
 pop es
 mov si,[bp+4]
 mov di,[bp+6]
 xor cx,cx
 mov ax,6000h
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
_viewer_kernel_attributes:
 enter
 mov dx,[bp+4]
 mov ax,4300h
 int 21h
 jc .done
 mov bx,[ss:bp+6]
 mov [ss:bx],cx
 xor ax,ax
.done:
 leave
_viewer_kernel_open:
 enter
 mov dx,[bp+4]
 mov ax,3da0h ; read-only, deny-write, private/no-inherit
 int 21h
 jc .done
 mov bx,[ss:bp+6]
 mov [ss:bx],ax
 xor ax,ax
.done:
 leave
_viewer_kernel_device:
 enter
 mov bx,[bp+4]
 mov ax,4400h
 int 21h
 jc .done
 mov bx,[ss:bp+6]
 mov [ss:bx],dx
 xor ax,ax
.done:
 leave
_viewer_kernel_read:
 enter
 mov bx,[bp+4]
 mov cx,[bp+10]
 lds dx,[bp+6]
 mov ah,3fh
 int 21h
 jc .done
 mov bx,[ss:bp+12]
 mov [ss:bx],ax
 xor ax,ax
.done:
 leave
_viewer_kernel_seek:
 enter
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ax,4200h
 int 21h
 jc .done
 mov bx,[ss:bp+10]
 mov [ss:bx],ax
 mov [ss:bx+2],dx
 xor ax,ax
.done:
 leave
_viewer_kernel_close:
 enter
 mov bx,[bp+4]
 mov ah,3eh
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
