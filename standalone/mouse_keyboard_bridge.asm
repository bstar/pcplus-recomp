; Diagnostic event producer on a private SS; the IRQ path remains native code.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern mouse_callback
global _mouse_test_emit,_mouse_test_prior_callback
global _mouse_test_prior_hits
_mouse_test_emit:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push ds
 push es
 pushf
 pop word [cs:saved_flags]
 mov ax,[bp+4]
 mov si,[bp+6]
 mov di,[bp+8]
 cli
 mov [cs:saved_ss],ss
 mov [cs:saved_sp],sp
 mov bx,seg foreign_top
 mov ss,bx
 mov sp,foreign_top
 mov bx,0x40
 mov ds,bx
 call far [cs:callback]
 mov bx,ds
 mov dx,ss
 mov ax,[cs:saved_ss]
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov ax,1
 cmp bx,0x40
 jne .bad
 mov bx,seg foreign_top
 cmp dx,bx
 jne .bad
 pushf
 pop bx
 test bx,0x200
 jz .done
.bad:
 xor ax,ax
.done:
 push word [cs:saved_flags]
 popf
 pop es
 pop ds
 pop di
 pop si
 pop bx
 pop bp
 ret
_mouse_test_prior_callback:
 inc word [cs:_mouse_test_prior_hits]
 retf
_mouse_test_prior_hits: dw 0
callback: dw mouse_callback,seg mouse_callback
saved_ss: dw 0
saved_sp: dw 0
saved_flags: dw 0
SEGMENT MOUSESTACK private align=16 class=DATA use16
resb 1024
foreign_top:
