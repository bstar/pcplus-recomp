BITS 16
CPU 8086
%ifdef TERMINAL_HOOK_MODEM
SEGMENT MODEM_CODE public align=16 class=FARCODE use16
extern terminal_modem_init_validate_plan_impl
global _hook_modem_init_plan
_hook_modem_init_plan:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 mov si,[bp+6]
 mov ax,[bp+8]
 call terminal_modem_init_validate_plan_impl
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _terminal_hook_modem_offer
_terminal_hook_modem_offer: times 1086 db 0
%endif
