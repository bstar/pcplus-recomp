BITS 16
CPU 8086
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _hook_input_probe_names
_hook_input_probe_names:
%macro name 1
 %%start: db %1,0
 times 20-($-%%start) db 0
%endmacro
name 'D:\CASE.BIN'
name 'D:\INPUTCH.EXE'
name 'D:\KEY0.BIN'
name 'D:\TABLE0.BIN'
name 'D:\LIVE0.BIN'
name 'D:\KEY1.BIN'
name 'D:\TABLE1.BIN'
name 'D:\LIVE1.BIN'
name 'D:\OFFER.BIN'
name 'D:\PROPOSAL.BIN'
name 'D:\BASE0.BIN'
name 'D:\BASE1.BIN'
name 'D:\PBEFORE.BIN'
name 'D:\PAFTER.BIN'
name 'D:\RESULTS.BIN'
name 'D:\STACK.BIN'
name 'D:\BANK0.BIN'
name 'D:\BANK1.BIN'
name 'D:\CWD.BIN'
name 'D:\EDIT0.BIN'
name 'D:\EDIT1.BIN'
global _hook_input_probe_cwd
_hook_input_probe_cwd:
 push bp
 mov bp,sp
 push dx
 push si
 mov si,[bp+6]
 xor dl,dl
 mov ah,0x47
 int 0x21
 jc .bad
 xor ax,ax
 jmp .done
.bad:
 mov ax,1
.done:
 pop si
 pop dx
 pop bp
 retf
global _hook_input_probe_read
; Far cdecl(path near, destination near, bytes). Exact fixture read/close.
_hook_input_probe_read:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 mov dx,[bp+6]
 mov ax,0x3d00
 int 0x21
 jc .bad
 mov bx,ax
 mov dx,[bp+8]
 mov cx,[bp+10]
 mov ah,0x3f
 int 0x21
 jc .close_bad
 cmp ax,[bp+10]
 jne .close_bad
 mov ah,0x3e
 int 0x21
 jc .bad
 xor ax,ax
 jmp .done
.close_bad:
 mov ah,0x3e
 int 0x21
.bad:
 mov ax,1
.done:
 pop di
 pop si
 pop bx
 pop bp
 retf
