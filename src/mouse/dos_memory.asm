; CRT-free DOS memory/vector backend. Caller must have released PSP maxalloc
; slack while retaining every resident segment. No guessed PSP shrink here.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _mouse_platform_allocate,_mouse_platform_release,_mouse_platform_vector
_mouse_platform_allocate:
 push bp
 mov bp,sp
 push bx
 push es
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 push si
 push di
 cmp word [mouse_allocation_strategy_held],0
 jne .failed
%endif
 mov bx,[bp+4]
 or bx,bx
 jz .failed
 mov ax,bx
 mov cl,4
 shr bx,cl
 and ax,15
 jz .aligned
 inc bx
.aligned:
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 ; Place the small saved-driver block at the high end, so it cannot divide
 ; an inactive frozen-history loan from the main free EXEC arena. DOS3+58h
 ; strategy is restored immediately, including allocation-error paths.
 mov si,bx
 mov ax,5800h
 int 21h
 jc .failed
 mov di,ax
 mov bx,2
 mov ax,5801h
 int 21h
 jc .failed
 mov bx,si
 mov ah,48h
 int 21h
 pushf
 push ax
 mov bx,di
 mov ax,5801h
 int 21h
 jc .strategy_failed
 pop ax
 popf
 jc .failed
 jmp .allocated
.strategy_failed:
 mov [mouse_allocation_strategy_error],ax
 mov [mouse_allocation_strategy_saved],di
 mov word [mouse_allocation_strategy_held],1
 pop ax
 pop cx
 test cx,1
 jnz .failed
 mov [mouse_allocation_strategy_segment],ax
 jmp .failed
.allocated:
%else
 mov ah,0x48
 int 0x21
 jc .failed
%endif
 mov dx,ax
 xor ax,ax
 jmp short .done
.failed:
 xor ax,ax
 xor dx,dx
.done:
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 pop di
 pop si
%endif
 pop es
 pop bx
 pop bp
 ret
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
; Failed strategy restoration never publishes the allocation to a driver.
; Retain its exact identity; shutdown may restore the strategy then release it
; once. An ambiguous free is quarantined, never blindly retried.
global _mouse_platform_strategy_finish
_mouse_platform_strategy_finish:
 push bx
 push es
 cmp word [mouse_allocation_strategy_held],0
 je .success
 cmp word [mouse_allocation_strategy_free_attempted],0
 jne .uncertain
 mov bx,[mouse_allocation_strategy_saved]
 mov ax,5801h
 int 21h
 jc .failed
 mov ax,[mouse_allocation_strategy_segment]
 or ax,ax
 jz .released
 mov es,ax
 mov word [mouse_allocation_strategy_free_attempted],1
 mov ah,49h
 int 21h
 jc .failed
.released:
 mov word [mouse_allocation_strategy_held],0
 mov word [mouse_allocation_strategy_segment],0
 mov word [mouse_allocation_strategy_error],0
 mov word [mouse_allocation_strategy_free_attempted],0
.success:
 xor ax,ax
 jmp .done
.uncertain:
 mov ax,9
 jmp .done
.failed:
 mov [mouse_allocation_strategy_error],ax
.done:
 pop es
 pop bx
 ret
SEGMENT _DATA public class=DATA use16
global mouse_allocation_strategy_held,mouse_allocation_strategy_saved
global mouse_allocation_strategy_segment,mouse_allocation_strategy_error
global mouse_allocation_strategy_free_attempted
mouse_allocation_strategy_held: dw 0
mouse_allocation_strategy_saved: dw 0
mouse_allocation_strategy_segment: dw 0
mouse_allocation_strategy_error: dw 0
mouse_allocation_strategy_free_attempted: dw 0
SEGMENT _TEXT
%endif
_mouse_platform_release:
 push bp
 mov bp,sp
 push bx
 push es
 cmp word [bp+4],0
 jne .invalid
 mov ax,[bp+6]
 or ax,ax
 jz .invalid
 mov es,ax
 mov ah,0x49
 int 0x21
 jc .done
 xor ax,ax
 jmp short .done
.invalid:
 mov ax,9
.done:
 pop es
 pop bx
 pop bp
 ret
_mouse_platform_vector:
 push bx
 push es
 mov ax,0x3533
 int 0x21
 mov ax,bx
 mov dx,es
 pop es
 pop bx
 ret
