; Register ABI for a private native-reset data/stack context. AX=request,
; return AX=body status or1 for rejected entry. All other registers and caller
; FLAGS are preserved. No application data image, UART state or DOS owner is
; restored. The native body owns its own projection and error policy.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
GROUP RESET_GROUP RESET_DATA
SEGMENT _TEXT public class=CODE use16
global reset_bank_call
reset_bank_call:
 call far reset_bank_call_far
 ret

SEGMENT RESET_CODE public align=16 class=FARCODE use16
extern reset_bank_body,reset_stack_top
global reset_bank_call_far,reset_bank_abort,reset_bank_request,reset_bank_busy
reset_bank_request: dw 0
reset_bank_busy: dw 0
saved_ss: dw 0
saved_sp: dw 0
result: dw 0

%macro restore 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
%endmacro

reset_bank_call_far:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 mov bx,sp
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .reject
 cmp ax,DGROUP
 jne .reject
 mov cx,[ss:bx+18]
 and cx,0x600
 cmp cx,0x200
 jne .reject
 cmp word [cs:reset_bank_busy],0
 jne .reject
 mov ax,[ss:bx+16]
 mov [cs:reset_bank_request],ax
 mov word [cs:reset_bank_busy],1
 mov [cs:saved_ss],ss
 mov [cs:saved_sp],sp
 cli
 mov ax,RESET_GROUP
 mov ss,ax
 mov sp,reset_stack_top
 mov ds,ax
 mov es,ax
 sti
 call reset_bank_body
 mov [cs:result],ax
 jmp .return
.reject:
 restore
 mov ax,1
 retf

reset_bank_abort:
 ; Only the admitted private body may abandon its own call frames here.
 mov [cs:result],ax
reset_bank_call_far.return:
 cli
 mov ax,[cs:saved_ss]
 mov ss,ax
 mov sp,[cs:saved_sp]
 mov word [cs:reset_bank_busy],0
 restore
 mov ax,[cs:result]
 retf
SEGMENT _DATA public align=16 class=DATA use16
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
SEGMENT RESET_DATA public align=16 class=DATA use16
