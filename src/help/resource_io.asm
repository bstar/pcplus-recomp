BITS 16
CPU 8086
SEGMENT NOTICEINPUT_CODE public align=16 class=FARCODE use16
global _help_file_open,_help_file_close,_help_file_size,_help_file_read
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
%endmacro
%macro leave 0
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
%endmacro
_help_file_open:
 enter
 mov dx,[bp+4]
 mov ax,0x3d00
 int 0x21
 jc .done
 mov bx,[bp+6]
 mov [bx],ax
 xor ax,ax
.done:
 leave
_help_file_close:
 enter
 mov bx,[bp+4]
 mov ah,0x3e
 int 0x21
 jc .done
 xor ax,ax
.done:
 leave
_help_file_size:
 enter
 mov bx,[bp+4]
 xor cx,cx
 xor dx,dx
 mov ax,0x4202
 int 0x21
 jc .done
 mov bx,[bp+6]
 mov [bx],ax
 mov [bx+2],dx
 xor ax,ax
.done:
 leave
_help_file_read:
 enter
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ax,0x4200
 int 0x21
 jc .done
 mov dx,[bp+10]
 mov cx,[bp+12]
 mov ah,0x3f
 int 0x21
 jc .done
 mov bx,[bp+14]
 mov [bx],ax
 xor ax,ax
.done:
 leave
