; cdecl near boundary within FILE_CODE. DS=SS on entry and return.
; Operation,spec,attribute,far DTA. DOS2F/1A preserve the caller's current DTA
; around one4E/4F call; the private43-byte DTA retains continuation state.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
global _file_find_kernel
_file_find_kernel:
 push bp
 mov bp,sp
 sub sp,6
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov ah,2fh
 int 21h
 mov [ss:bp-4],bx
 mov [ss:bp-2],es
 push ds
 mov dx,[bp+10]
 mov ds,[bp+12]
 mov ah,1ah
 int 21h
 pop ds
 mov ax,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 int 21h
 jc .error
 xor ax,ax
.error:
 mov [ss:bp-6],ax
 push ds
 lds dx,[ss:bp-4]
 mov ah,1ah
 int 21h
 pop ds
 mov ax,[ss:bp-6]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 ret
