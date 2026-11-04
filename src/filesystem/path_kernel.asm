; Maintained cdecl DOS boundary. DS=SS; preserves all non-result registers.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern file_path_native_change
global _path_native_change,_path_current_drive,_path_select_drive,_path_getcwd
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
_path_native_change:
 enter
 push word [bp+4]
 call file_path_native_change
 leave
_path_current_drive:
 enter
 mov ah,0x19
 int 0x21
 xor ah,ah
 leave
_path_select_drive:
 enter
 mov dx,[bp+4]
 mov ah,0x0e
 int 0x21
 mov ah,0x19
 int 0x21
 xor ah,ah
 leave
_path_getcwd:
 enter
 mov dx,[bp+4]
 inc dx
 mov si,[bp+6]
 mov ah,0x47
 int 0x21
 jc .return
 xor ax,ax
.return:
 leave
