BITS 16
CPU 8086
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _hook_probe_write
; Far cdecl(path near, source far, bytes word). No CRT startup or buffering.
_hook_probe_write:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 push ds
 mov dx,[bp+6]
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .error
 mov bx,ax
 mov cx,[bp+12]
 mov si,cx
 mov dx,[bp+8]
 mov ds,[bp+10]
 mov ah,0x40
 int 0x21
 jc .close_error
 cmp ax,si
 jne .close_error
 mov ah,0x3e
 int 0x21
 jc .error
 xor ax,ax
 jmp .done
.close_error:
 mov ah,0x3e
 int 0x21
.error:
 mov ax,1
.done:
 pop ds
 pop es
 pop di
 pop si
 pop bx
 pop bp
 retf
global _hook_probe_names
_hook_probe_names:
%macro name 1
 %%start: db %1,0
 times 13-($-%%start) db 0
%endmacro
name 'HOOKCH.EXE'
name 'STAGE0.BIN'
name 'RBFORE.BIN'
name 'BASE0.BIN'
name 'RBAGAIN.BIN'
name 'BASE1.BIN'
name 'RESULTS.BIN'
name 'ABSENT.EXE'
name 'DIAG.BIN'
name 'STACK.BIN'
name 'MODEM0.BIN'
name 'MSTAT.BIN'
extern terminal_stack_top
global _hook_probe_stack
_hook_probe_stack:
 mov ax,terminal_stack_top-8192
 retf
