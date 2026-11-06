; Fixture-only FAR calls using the loaded parent's real DS=SS/declared stack.
; No product instruction is patched. Caller words and results use CS scratch
; while DS/SS belong to the parent. Restore original SS:SP with IF masked.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _chat_parent_invoke
_chat_parent_invoke:
 push bp
 mov bp,sp
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov bx,[bp+4]
 xor si,si
.copy:
 mov ax,[bx+si]
 mov [cs:control+si],ax
 add si,2
 cmp si,28
 jb .copy
 mov [cs:saved_ss],ss
 mov [cs:saved_sp],sp
 mov ax,[cs:control]
 cli
 mov ss,ax
 mov sp,[cs:control+2]
 mov ds,ax
 mov es,ax
 mov ax,0x202
 push ax
 popf
 mov si,[cs:control+10]
 shl si,1
 jz .arguments_ready
.arguments:
 sub si,2
 push word [cs:control+12+si]
 or si,si
 jnz .arguments
.arguments_ready:
 mov ax,[cs:control+8]
 call far [cs:control+4]
 mov [cs:result_ax],ax
 pushf
 pop ax
 mov [cs:result_flags],ax
 cli
 mov ax,[cs:saved_ss]
 mov ss,ax
 mov sp,[cs:saved_sp]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 mov bx,[bp+4]
 mov ax,[cs:result_ax]
 mov [bx+28],ax
 mov ax,[cs:result_flags]
 mov [bx+30],ax
 pop bx
 popf
 pop bp
 mov ax,[cs:result_ax]
 ret
control: times 14 dw 0
saved_ss: dw 0
saved_sp: dw 0
result_ax: dw 0
result_flags: dw 0
