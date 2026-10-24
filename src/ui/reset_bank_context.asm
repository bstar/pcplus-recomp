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
%ifdef RESET_BANK_OVERLAY
extern redisplay_snapshot,_redisplay_active,_redisplay_export_pending,_redisplay_search_pending
extern _command_menu_active,terminal_snapshot_active,terminal_program_active,terminal_program_pending
extern terminal_monitor_active,terminal_controller_active,terminal_transfer_active,terminal_transfer_pending
%endif
%ifdef RESET_BANK_TRANSACTION
extern reset_live_active,terminal_width_aspect_owner_far
%endif
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
%ifdef RESET_BANK_TRANSACTION
 mov ax,[ss:bx+16]
 cmp ax,0x100
 je .live_owner
 cmp ax,0x101
 je .live_owner
 cmp word [cs:reset_live_active],0
 jne .reject
 jmp .owner_checked
.live_owner:
 cmp word [cs:reset_live_active],1
 jne .reject
.owner_checked:
%endif
%ifdef RESET_BANK_OVERLAY
 mov ax,[_redisplay_active]
 or ax,[_redisplay_export_pending]
 or ax,[_redisplay_search_pending]
 or ax,[_command_menu_active]
 or ax,[terminal_snapshot_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_transfer_active]
 or ax,[terminal_transfer_pending]
 jnz .reject
 cmp word [terminal_program_active],0
 je .program_checked
%ifdef RESET_BANK_TRANSACTION
 ; The live transaction already owns a separate rollback frame. Do not lend
 ; the native workspace to arbitrary PROGRAM or cold-reset callers.
 cmp word [cs:reset_live_active],1
 jne .reject
 mov ax,[ss:bx+16]
 cmp ax,0x100
 je .aspect_owner
 cmp ax,0x101
 jne .reject
.aspect_owner:
 call far terminal_width_aspect_owner_far
 jc .reject
%else
 jmp .reject
%endif
.program_checked:
%endif
 mov ax,[ss:bx+16]
 mov [cs:reset_bank_request],ax
 mov word [cs:reset_bank_busy],1
 mov [cs:saved_ss],ss
 mov [cs:saved_sp],sp
 cli
%ifdef RESET_BANK_OVERLAY
 mov ax,seg redisplay_snapshot
%else
 mov ax,RESET_GROUP
%endif
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
%ifdef RESET_BANK_APP
SEGMENT RESET_DATA public align=16 class=NATIVE_DATA use16
%else
SEGMENT RESET_DATA public align=16 class=DATA use16
%endif
