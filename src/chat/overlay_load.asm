; Cdecl near helper: path near in the parent's DS, paragraph load/reloc segment.
; DOS overlay mode does not create a PSP or transfer control. AX0 or DOS error.
BITS 16
CPU 8086
%ifdef CHAT_LOADER_BANK
SEGMENT CHAT_LOAD_CODE public align=16 class=FARCODE use16
GROUP CHAT_LOAD_GROUP CHAT_LOAD_CODE
%else
SEGMENT _TEXT public class=CODE use16
%endif
global _chat_dos_overlay_load
global _chat_file_open,_chat_file_read,_chat_file_close
_chat_file_open:
 push bp
 mov bp,sp
 push bx
 push dx
 mov dx,[bp+4]
 mov ax,0x3d00
 int 0x21
 jc .done
 mov bx,[bp+6]
 mov [bx],ax
 xor ax,ax
.done:
 pop dx
 pop bx
 pop bp
 ret
_chat_file_read:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ah,0x3f
 int 0x21
 jc .done
 mov bx,[bp+10]
 mov [bx],ax
 xor ax,ax
.done:
 pop dx
 pop cx
 pop bx
 pop bp
 ret
_chat_file_close:
 push bp
 mov bp,sp
 push bx
 mov bx,[bp+4]
 mov ah,0x3e
 int 0x21
 jc .done
 xor ax,ax
.done:
 pop bx
 pop bp
 ret
_chat_dos_overlay_load:
 push bp
 mov bp,sp
 push bx
 push dx
 push si
 push di
 push es
 push ds
 sub sp,4
 mov bx,sp
 mov ax,[bp+6]
 mov [ss:bx],ax
 mov [ss:bx+2],ax
 mov ax,ss
 mov es,ax
 mov dx,[bp+4]
 mov ax,0x4b03
 int 0x21
 jc .done
 xor ax,ax
.done:
 add sp,4
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop bx
 pop bp
 ret
