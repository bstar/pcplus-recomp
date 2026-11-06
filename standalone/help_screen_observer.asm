; Diagnostic BIOS keyboard boundary: capture the visible text before supplying
; each scripted read. No helper addresses, memory patches, DOS calls or file
; writes from the handler. Only the temporary INT16 vector is owned.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _help_screen_begin,_help_screen_end,_help_screen_count,_help_screen_metadata
saved: dw 0,0
base: dw 0
count: dw 0
index: dw 0
keys: times 64 dw 27
positions: times 32 dw 0
shapes: times 32 dw 0
handler:
 cmp ah,0
 je .read
 cmp ah,0x10
 je .read
 cmp ah,1
 je .peek
 cmp ah,0x11
 jne .chain
.peek:
 push bp
 mov bp,sp
 push bx
 mov bx,[cs:index]
 shl bx,1
 mov ax,[cs:keys+bx]
 pop bx
 and word [ss:bp+6],0xffbf
 pop bp
 iret
.chain:
 jmp far [cs:saved]
.read:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 cmp word [cs:count],32
 jae .key
 mov ax,0x40
 mov ds,ax
 mov bx,[cs:count]
 shl bx,1
 mov ax,[0x50]
 mov [cs:positions+bx],ax
 mov ax,[0x60]
 mov [cs:shapes+bx],ax
 xor ax,ax
 mov al,[0x84]
 inc ax
 cmp ax,50
 ja .key
 mov dx,80
 mul dx
 mov cx,ax
 mov ax,[cs:count]
 mov dx,500
 mul dx
 add ax,[cs:base]
 mov es,ax
 mov ax,0xb800
 mov ds,ax
 xor si,si
 xor di,di
 cld
 rep movsw
 inc word [cs:count]
.key:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 push bx
 mov bx,[cs:index]
 shl bx,1
 mov ax,[cs:keys+bx]
 cmp word [cs:index],63
 jae .last
 inc word [cs:index]
.last:
 pop bx
 and word [ss:bp+6],0xffbf
 pop bp
 iret
_help_screen_begin:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,[bp+4]
 mov [cs:base],ax
 mov word [cs:count],0
 mov word [cs:index],0
 mov si,[bp+6]
 push cs
 pop es
 mov di,keys
 mov cx,64
 cld
 rep movsw
 mov ax,0x3516
 int 0x21
 mov [cs:saved],bx
 mov [cs:saved+2],es
 push ds
 push cs
 pop ds
 mov dx,handler
 mov ax,0x2516
 int 0x21
 pop ds
 pop es
 pop di
 pop si
 pop bp
 ret
_help_screen_end:
 push ds
 mov dx,[cs:saved]
 mov ds,[cs:saved+2]
 mov ax,0x2516
 int 0x21
 pop ds
 ret
_help_screen_count:
 mov ax,[cs:count]
 ret
_help_screen_metadata:
 push bp
 mov bp,sp
 push bx
 push si
 mov bx,[bp+4]
 shl bx,1
 mov si,[bp+6]
 mov ax,[cs:positions+bx]
 mov [si],ax
 mov si,[bp+8]
 mov ax,[cs:shapes+bx]
 mov [si],ax
 pop si
 pop bx
 pop bp
 ret
