; Test-only independent current-DTA/foreign-enumeration endpoint.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _find_probe_get,_find_probe_set,_find_probe_first,_find_probe_next
_find_probe_get:
 push bp
 mov bp,sp
 push bx
 push si
 push es
 mov ah,2fh
 int 21h
 mov si,[bp+4]
 mov [si],bx
 mov [si+2],es
 pop es
 pop si
 pop bx
 pop bp
 ret
_find_probe_set:
 push bp
 mov bp,sp
 push dx
 push ds
 lds dx,[bp+4]
 mov ah,1ah
 int 21h
 pop ds
 pop dx
 pop bp
 ret
_find_probe_first:
 push bp
 mov bp,sp
 push cx
 push dx
 mov dx,[bp+4]
 xor cx,cx
 mov ax,4e00h
 int 21h
 jc .done
 xor ax,ax
.done:
 pop dx
 pop cx
 pop bp
 ret
_find_probe_next:
 mov ah,4fh
 int 21h
 jc .done
 xor ax,ax
.done:
 ret
