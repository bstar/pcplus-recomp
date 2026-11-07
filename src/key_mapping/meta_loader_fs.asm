; Loader-only private kernel. FILE_CODE stays resident while META is absent.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
GROUP FILE_GROUP FILE_CODE
%ifdef META_LOADER_FAULTS
%define _meta_load_fs_open _meta_load_real_open
%define _meta_load_fs_read _meta_load_real_read
%define _meta_load_fs_close _meta_load_real_close
%endif
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
global _meta_load_fs_open,_meta_load_fs_read,_meta_load_fs_close
_meta_load_fs_open:
 enter
 mov dx,[bp+4]
 mov ax,3da0h
 int 21h
 jc .done
 mov bx,[bp+6]
 mov [bx],ax
 xor ax,ax
.done:leave
_meta_load_fs_read:
 enter
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+10]
 mov ds,[bp+8]
 mov ah,3fh
 int 21h
 push ss
 pop ds
 jc .done
 mov bx,[bp+12]
 mov [bx],ax
 xor ax,ax
.done:leave
_meta_load_fs_close:
 enter
 mov bx,[bp+4]
 mov ah,3eh
 int 21h
 jc .done
 xor ax,ax
.done:leave
