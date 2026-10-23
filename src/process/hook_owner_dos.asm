; HOOK_CODE-local DOS memory and direct EXEC adapters, DS=SS.
; Caller initializes trusted PSP/minimum/keep counts for every resident bank.
BITS 16
CPU 8086
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
extern process_psp,process_minimum_paragraphs,process_keep_paragraphs
extern process_memory_released,process_busy,process_run_far
global _hook_platform_psp,_hook_platform_prepare,_hook_platform_allocate
global _hook_platform_release,_hook_platform_execute,_hook_platform_busy
_hook_platform_psp:
 push bx
 mov ah,0x51
 int 0x21
 mov ax,bx
 pop bx
 ret
_hook_platform_busy:
 mov ax,[process_busy]
 ret
_hook_platform_prepare:
 push bx
 push es
 cmp word [process_busy],0
 jne .invalid
 call _hook_platform_psp
 cmp ax,[process_psp]
 jne .invalid
 cmp ax,0
 je .invalid
 mov bx,[process_keep_paragraphs]
 cmp bx,[process_minimum_paragraphs]
 jb .invalid
 cmp bx,16
 jb .invalid
 ; A trusted complete layout is still required, but never shrink below
 ; the actual executing stack even if the caller supplies a bad minimum.
 push ax
 push dx
 mov dx,ss
 sub dx,ax
 jc .bad_stack
 mov ax,sp
 add ax,16
 jc .bad_stack
 add ax,15
 jc .bad_stack
 mov cl,4
 shr ax,cl
 add dx,ax
 jc .bad_stack
 cmp bx,dx
 jb .bad_stack
 pop dx
 pop ax
 jmp short .stack_ok
.bad_stack:
 pop dx
 pop ax
 jmp .invalid
.stack_ok:
 cmp word [process_memory_released],0
 jne .ok
%ifdef HOOK_OWNER_DIAGNOSTIC
 cmp word [cs:_hook_test_resize],0
 jne .memory
%endif
 mov es,ax
 mov ah,0x4a
 int 0x21
 jc .done
 mov word [process_memory_released],1
.ok:
 xor ax,ax
 jmp .done
.invalid:
 mov ax,9
 jmp .done
%ifdef HOOK_OWNER_DIAGNOSTIC
.memory:
 mov ax,8
%endif
.done:
 pop es
 pop bx
 ret
_hook_platform_allocate:
 push bp
 mov bp,sp
 push bx
 push es
%ifdef HOOK_OWNER_DIAGNOSTIC
 cmp word [cs:_hook_test_allocate],0
 jne .failed
%endif
 mov bx,[bp+4]
 mov ah,0x48
 int 0x21
 jc .done
 mov bx,[bp+6]
 mov [bx],ax
 xor ax,ax
 jmp .done
%ifdef HOOK_OWNER_DIAGNOSTIC
.failed:
 mov ax,8
%endif
.done:
 pop es
 pop bx
 pop bp
 ret
_hook_platform_release:
 push bp
 mov bp,sp
 push bx
 push es
%ifdef HOOK_OWNER_DIAGNOSTIC
 cmp word [cs:_hook_test_release],0
 jne .failed
%endif
 mov es,[bp+4]
 mov ah,0x49
 int 0x21
 jc .done
 xor ax,ax
 jmp .done
%ifdef HOOK_OWNER_DIAGNOSTIC
.failed:
 mov ax,9
%endif
.done:
 pop es
 pop bx
 pop bp
 ret
_hook_platform_execute:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far process_run_far
 mov sp,bp
 pop bp
 ret
%ifdef HOOK_OWNER_DIAGNOSTIC
global _hook_test_resize,_hook_test_allocate,_hook_test_release
_hook_test_resize: dw 0
_hook_test_allocate: dw 0
_hook_test_release: dw 0
%endif
