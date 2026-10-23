BITS 16
CPU 8086
%ifdef TERMINAL_SESSION_BASELINE
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
extern terminal_configuration_values
global _hook_baseline_invalidate,_hook_baseline_publish,_hook_baseline_copy
%macro save 0
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
%endmacro
%macro restore 0
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endmacro
baseline_context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,seg terminal_configuration_values
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 test ax,0x400
 jnz .bad
 test ax,0x200
 jz .bad
 clc
 ret
.bad:
 stc
 ret
_hook_baseline_invalidate:
 save
 call baseline_context
 jc .context
 mov word [cs:terminal_baseline_valid],0
 mov word [cs:terminal_baseline_kind],0
 mov word [cs:terminal_baseline_checksum],0
 xor ax,ax
 jmp .done
.context:
 mov ax,2
.done:
 restore
_hook_baseline_publish:
 save
 call baseline_context
 jc .context
 mov si,[bp+6]
 or si,si
 jz .argument
 cmp si,65536-1264
 ja .argument
 mov ax,[bp+8]
 cmp ax,1
 jb .argument
%ifdef TERMINAL_HOOK_APPLY
 cmp ax,3
%else
 cmp ax,2
%endif
 ja .argument
 mov bx,[cs:terminal_baseline_generation]
 inc bx
 jnz .generation
 inc bx
.generation:
 mov dx,0xb41d
 xor dx,bx
 xor dx,ax
 mov word [cs:terminal_baseline_valid],0
 push cs
 pop es
 mov di,terminal_baseline_image
 mov cx,632
.copy:
 lodsw
 stosw
 rol dx,1
 xor dx,ax
 loop .copy
 mov [cs:terminal_baseline_generation],bx
 mov ax,[bp+8]
 mov [cs:terminal_baseline_kind],ax
 mov [cs:terminal_baseline_checksum],dx
 mov word [cs:terminal_baseline_valid],0xb451
 xor ax,ax
 jmp .done
.argument:
 mov ax,1
 jmp .done
.context:
 mov ax,2
.done:
 restore
_hook_baseline_copy:
 save
 call baseline_context
 jc .context
 mov di,[bp+6]
 or di,di
 jz .argument
 cmp di,65536-1264
 ja .argument
 cmp word [cs:terminal_baseline_valid],0xb451
 jne .missing
 mov bx,[cs:terminal_baseline_generation]
 or bx,bx
 jz .damaged
 mov ax,[cs:terminal_baseline_kind]
 cmp ax,1
 jb .damaged
%ifdef TERMINAL_HOOK_APPLY
 cmp ax,3
%else
 cmp ax,2
%endif
 ja .damaged
 mov dx,0xb41d
 xor dx,bx
 xor dx,ax
 mov si,terminal_baseline_image
 mov cx,632
.seal:
 mov ax,[cs:si]
 add si,2
 rol dx,1
 xor dx,ax
 loop .seal
 cmp dx,[cs:terminal_baseline_checksum]
 jne .damaged
 push ds
 pop es
 push cs
 pop ds
 mov si,terminal_baseline_image
 mov cx,632
 rep movsw
 xor ax,ax
 jmp .done
.argument:
 mov ax,1
 jmp .done
.context:
 mov ax,2
 jmp .done
.missing:
 mov ax,3
 jmp .done
.damaged:
 mov ax,4
.done:
 restore
global terminal_baseline_storage,terminal_baseline_storage_end
global terminal_baseline_valid,terminal_baseline_generation,terminal_baseline_kind
global terminal_baseline_checksum,terminal_baseline_image
terminal_baseline_storage:
terminal_baseline_valid: dw 0
terminal_baseline_generation: dw 0
terminal_baseline_kind: dw 0
terminal_baseline_checksum: dw 0
terminal_baseline_image: times 1264 db 0
terminal_baseline_storage_end:
%endif
