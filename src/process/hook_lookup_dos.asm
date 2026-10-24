; HOOK_CODE-local DOS boundaries. No C runtime, allocation or active UART I/O.
BITS 16
CPU 8086
%ifdef TERMINAL_HOOK_LOOKUP
SEGMENT _DATA public class=DATA use16
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
GROUP DGROUP _DATA
extern process_run_far
global _hook_lookup_context,_hook_lookup_readable,_hook_lookup_access,_hook_lookup_raw
global _hook_lookup_cancelled
_hook_lookup_cancelled:
%ifdef TERMINAL_TRAPS
 extern terminal_trap_poll,terminal_quit
 call far terminal_trap_poll
 mov ax,[terminal_quit]
%else
 xor ax,ax
%endif
 ret
_hook_lookup_context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,DGROUP
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 test ax,0x400
 jnz .bad
 test ax,0x200
 jz .bad
 mov ax,1
 ret
.bad:
 xor ax,ax
 ret
_hook_lookup_readable:
 push bp
 mov bp,sp
 push bx
 mov dx,[bp+4]
 mov ax,0x3d00
 int 0x21
 jc .done
 mov bx,ax
 mov ah,0x3e
 int 0x21
 xor ax,ax
.done:
 pop bx
 pop bp
 ret
_hook_lookup_access:
 push bp
 mov bp,sp
 push cx
 mov dx,[bp+4]
 mov ax,0x4300
 int 0x21
 jc .done
 xor ax,ax
.done:
 pop cx
 pop bp
 ret
_hook_lookup_raw:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far process_run_far
 mov sp,bp
 pop bp
 ret
%endif
