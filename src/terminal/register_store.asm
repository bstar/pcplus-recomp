BITS 16
CPU 8086
%ifdef TERMINAL_REGISTER_HANDOFF
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
extern _script_handoff
global _terminal_register_owner,terminal_register_storage_end
global _terminal_register_context
_terminal_register_context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,seg _script_handoff
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 mov ax,1
 retf
.bad:
 xor ax,ax
 retf
_terminal_register_owner: times 1734 db 0
terminal_register_storage_end:
%endif
