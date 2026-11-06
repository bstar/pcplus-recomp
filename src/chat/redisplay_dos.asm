; Loaded bank DOS arena services, parent DS=SS and caller-owned stack.
BITS 16
CPU 8086
SEGMENT CHAT_CODE public align=16 class=FARCODE use16
global _chat_view_allocate,_chat_view_free
_chat_view_allocate:
 push bp
 mov bp,sp
 push bx
 mov bx,[bp+6]
 mov ah,0x48
 int 0x21
 jnc .done
 xor ax,ax
.done:
 pop bx
 pop bp
 retf
_chat_view_free:
 push bp
 mov bp,sp
 push es
 mov es,[bp+6]
 mov ah,0x49
 int 0x21
 jc .done
 xor ax,ax
.done:
 pop es
 pop bp
 retf
