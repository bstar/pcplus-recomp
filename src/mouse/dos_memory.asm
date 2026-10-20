; CRT-free DOS memory/vector backend. Caller must have released PSP maxalloc
; slack while retaining every resident segment. No guessed PSP shrink here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _mouse_platform_allocate,_mouse_platform_release,_mouse_platform_vector
_mouse_platform_allocate:
 push bp
 mov bp,sp
 push bx
 push es
 mov bx,[bp+4]
 or bx,bx
 jz .failed
 mov ax,bx
 mov cl,4
 shr bx,cl
 and ax,15
 jz .aligned
 inc bx
.aligned:
 mov ah,0x48
 int 0x21
 jc .failed
 mov dx,ax
 xor ax,ax
 jmp short .done
.failed:
 xor ax,ax
 xor dx,dx
.done:
 pop es
 pop bx
 pop bp
 ret
_mouse_platform_release:
 push bp
 mov bp,sp
 push bx
 push es
 cmp word [bp+4],0
 jne .invalid
 mov ax,[bp+6]
 or ax,ax
 jz .invalid
 mov es,ax
 mov ah,0x49
 int 0x21
 jc .done
 xor ax,ax
 jmp short .done
.invalid:
 mov ax,9
.done:
 pop es
 pop bx
 pop bp
 ret
_mouse_platform_vector:
 push bx
 push es
 mov ax,0x3533
 int 0x21
 mov ax,bx
 mov dx,es
 pop es
 pop bx
 ret
