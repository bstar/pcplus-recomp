; Child-owned stack half of resident render RPC. No parent data assumptions.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern __STACKLOW,__STACKTOP
extern _aspect_render_parent_entry,_aspect_render_callback_dispatch
global _aspect_render_client_prepare,_aspect_render_client_check
global _aspect_render_request,_aspect_render_callback_offset,_aspect_render_code_segment
_aspect_render_callback_offset: mov ax,aspect_render_callback
 ret
_aspect_render_code_segment: mov ax,cs
 ret
_aspect_render_client_prepare:
 push bx
 push dx
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov [cs:client_ds],ax
 mov bx,[__STACKLOW]
 mov ax,[__STACKTOP]
 sub ax,bx
 jc .bad
 ; Watcom reserves startup words inside the 8192-byte allocation.
 ; Require at least 7680 usable bytes plus the live-SP admission below.
 cmp ax,7680
 jb .bad
 mov dx,bx
 add dx,2048
 jc .bad
 mov ax,sp
 sub ax,dx
 jc .bad
 cmp ax,512
 jb .bad
 mov [cs:client_low],bx
 mov [cs:client_high],dx
 mov word [bx],0x3a51
 mov word [bx+2],0xc5ae
 mov bx,dx
 mov word [bx-4],0x6b92
 mov word [bx-2],0x946d
 sub dx,16
 mov [cs:client_top],dx
 mov byte [cs:callback_depth],0
 xor ax,ax
 jmp .done
.bad: mov ax,10
.done: pop dx
 pop bx
 ret
_aspect_render_client_check:
 push bx
 mov ax,ds
 cmp ax,[cs:client_ds]
 jne .bad
 mov ax,ss
 cmp ax,[cs:client_ds]
 jne .bad
 mov bx,[cs:client_low]
 cmp word [bx],0x3a51
 jne .bad
 cmp word [bx+2],0xc5ae
 jne .bad
 mov bx,[cs:client_high]
 cmp word [bx-4],0x6b92
 jne .bad
 cmp word [bx-2],0x946d
 jne .bad
 add bx,256
 jc .bad
 cmp sp,bx
 jb .bad
 xor ax,ax
 jmp .done
.bad: mov ax,10
.done: pop bx
 ret
_aspect_render_request:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,[bp+4]
 mov bx,[bp+6]
 call far [_aspect_render_parent_entry]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

; Parent AX=callbackop,BX=value. Preserve every register except resultAX and
; original FLAGS (including IF/DF); callbacks execute on lower child stack.
aspect_render_callback:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 ; Original FLAGS are already saved. No interrupt may observe child DS
 ; paired with the still-parent SS during validation/stack transition.
 cli
 cmp byte [cs:callback_depth],0
 jne .reject
 mov [cs:callback_op],ax
 mov [cs:callback_value],bx
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .reject
 mov ax,[cs:client_ds]
 or ax,ax
 jz .reject
 mov ds,ax
 mov bx,[cs:client_low]
 cmp word [bx],0x3a51
 jne .reject
 cmp word [bx+2],0xc5ae
 jne .reject
 mov bx,[cs:client_high]
 cmp word [bx-4],0x6b92
 jne .reject
 cmp word [bx-2],0x946d
 jne .reject
 mov bp,sp
 mov ax,[ss:bp+16]
 mov [cs:callback_flags],ax
 mov ax,ss
 mov [cs:parent_ss],ax
 mov [cs:parent_sp],sp
 mov byte [cs:callback_depth],1
 cli
 mov ax,[cs:client_ds]
 mov ss,ax
 mov sp,[cs:client_top]
 mov es,ax
 cld
 test word [cs:callback_flags],0x200
 jz .dispatch
 sti
.dispatch:
 push word [cs:callback_value]
 push word [cs:callback_op]
 call _aspect_render_callback_dispatch
 add sp,4
 mov [cs:callback_result],ax
 cli
 mov ax,[cs:parent_ss]
 mov ss,ax
 mov sp,[cs:parent_sp]
 mov byte [cs:callback_depth],0
 mov ax,[cs:callback_result]
 jmp .return
.reject: mov ax,10
.return:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf
client_ds: dw 0
client_low: dw 0
client_high: dw 0
client_top: dw 0
parent_ss: dw 0
parent_sp: dw 0
callback_op: dw 0
callback_value: dw 0
callback_flags: dw 0
callback_result: dw 0
callback_depth: db 0
SEGMENT _DATA public class=DATA use16
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
GROUP DGROUP _DATA _BSS STACK
