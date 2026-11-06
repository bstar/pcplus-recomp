; Near cdecl inside the loadable module. DS=SS; preserve all caller registers.
BITS 16
CPU 8086
SEGMENT CHAT_CODE public align=16 class=FARCODE use16
global _chat_present_get_cursor,_chat_present_set_cursor
%macro enter 0
 push bp
 mov bp,sp
 push ds
 push es
 push si
 push di
 push ax
 push bx
 push cx
 push dx
%endmacro
%macro leave 0
 pop dx
 pop cx
 pop bx
 pop ax
 pop di
 pop si
 pop es
 pop ds
 pop bp
 ret
%endmacro
_chat_present_get_cursor:
 enter
 xor bh,bh
 mov ah,3
 int 0x10
 mov bx,[ss:bp+4]
 mov [ss:bx],dx
 mov bx,[ss:bp+6]
 mov [ss:bx],cx
 leave
_chat_present_set_cursor:
 enter
 mov cx,[ss:bp+6]
 mov ah,1
 int 0x10
 mov dx,[ss:bp+4]
 xor bh,bh
 mov ah,2
 int 0x10
 leave
