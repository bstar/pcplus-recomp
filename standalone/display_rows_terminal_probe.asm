; Diagnostic only; all code is banked, with no resident helper bytes.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
global _rows_probe_write
; Far cdecl(name near,buffer near,count); DS=SS. Exclusive create, one close.
_rows_probe_write:
 push bp
 mov bp,sp
 sub sp,2
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov word [bp-2],1
 mov dx,[bp+6]
 xor cx,cx
 mov ax,0x5b00
 int 0x21
 jc .done
 mov bx,ax
 mov dx,[bp+8]
 mov cx,[bp+10]
 mov ah,0x40
 int 0x21
 jc .close
 cmp ax,[bp+10]
 jne .close
 mov word [bp-2],0
.close:
 mov ah,0x3e
 int 0x21
 jnc .done
 mov word [bp-2],1
.done:
 mov ax,[bp-2]
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf
