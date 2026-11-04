; Maintained manual Init foreground admission, keyboard lease and cleanup.
; CONFIG bank; owner remains MODEM_CODE. DS=SS. No settings/file edits.
BITS 16
CPU 8086
%ifdef TERMINAL_MANUAL_INIT
%include "modem_import.inc"
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern terminal_manual_init_active,terminal_manual_init_needs_resync
extern terminal_manual_init_begin_far,terminal_manual_init_cancel_far
extern terminal_modem_settings,connection_resync
extern terminal_control_defer_far

global terminal_manual_init_configured_far
terminal_manual_init_configured_far:
 push ax
 push cx
 push dx
 push si
 ; ceil(seconds *1193182/65536), saturating to owner's WORD tick budget.
 mov si,[terminal_modem_settings+MI_TIMEOUT]
 mov ax,si
 mov cx,18
 mul cx
 mov cx,ax
 push dx
 mov ax,si
 mov dx,13534
 mul dx
 add cx,dx
 pop dx
 adc dx,0
 or ax,ax
 jz .rounded
 add cx,1
 adc dx,0
.rounded:
 or dx,dx
 jz .bounded
 mov cx,0xffff
.bounded:
 or cx,cx
 jnz .budget
 inc cx
.budget:
 mov ax,cx
 mov si,terminal_modem_settings+MI_INITIALIZATION
 mov cx,MI_INITIALIZATION_SIZE
 mov dl,[terminal_modem_settings+MI_PAUSE_CHARACTER]
 call far terminal_manual_init_begin_far
 call far terminal_manual_init_sync_far
 pop si
 pop dx
 pop cx
 pop ax
 retf

; Existing retry separator is owned by connection startup, not manual Init.
global terminal_manual_init_sync_far
terminal_manual_init_sync_far:
 cmp word [terminal_manual_init_active],0
 jne .done
 cmp word [terminal_manual_init_needs_resync],0
 je .done
 mov byte [connection_resync],1
 mov word [terminal_manual_init_needs_resync],0 ; debt transferred, not forgotten
.done:
 retf

; Typed reason AX3/7/8, preserve AX for original connection action arguments.
global terminal_manual_init_stop_far
terminal_manual_init_stop_far:
 pushf
 push ax
 call far terminal_manual_init_cancel_far
 call far terminal_manual_init_sync_far
 pop ax
 popf
 retf

; CF1 consumes/defers; CF0 passes unchanged key to ordinary dispatcher.
; The foreground FIFO is not drained until the command releases its lease.
global terminal_manual_init_key_far
terminal_manual_init_key_far:
 cmp word [terminal_manual_init_active],0
 je .pass
 cmp ax,0x2400
 je .consumed ; repeated Alt-J never replaces or queues another initialization
 cmp ax,0x2d00
 je .exit
 cmp ax,0x2300
 je .hangup
 cmp al,27
 je .cancel
 call far terminal_control_defer_far
.consumed:
 stc
 retf
.cancel:
 push ax
 mov ax,3
 call far terminal_manual_init_stop_far
 pop ax
 jmp .consumed
.exit:
 push ax
 mov ax,8
 call far terminal_manual_init_stop_far
 pop ax
 jmp .pass
.hangup:
 push ax
 mov ax,3
 call far terminal_manual_init_stop_far
 pop ax
.pass:
 clc
 retf
%endif
