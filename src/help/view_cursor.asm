BITS 16
CPU 8086
SEGMENT NOTICEINPUT_CODE public align=16 class=FARCODE use16
global _help_view_cursor
_help_view_cursor:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov cx,[bp+6]
 mov ah,1
 int 0x10
 mov dx,[bp+4]
 xor bx,bx
 mov ah,2
 int 0x10
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
