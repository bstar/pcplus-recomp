; Application-owned DOS3+ break/critical traps. Handlers never call DOS.
BITS 16
CPU 8086
%ifdef TERMINAL_TRAPS
GROUP DGROUP _DATA
SEGMENT TRAP_CODE public align=16 class=FARCODE use16
GROUP TRAP_GROUP TRAP_CODE
extern process_psp,terminal_quit,terminal_exit_code
global terminal_trap_open,terminal_trap_suspend,terminal_trap_resume,terminal_trap_close
global terminal_trap_poll,terminal_trap_break,terminal_trap_critical,terminal_trap_hold
%macro save 0
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endmacro
context:
 call segments
 jc .bad
 pushf
 pop ax
 test ax,0x200
 jz .bad
 clc
 ret
.bad:
 stc
 ret
segments:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,DGROUP
 cmp ax,dx
 jne .bad
 clc
 ret
.bad:
 stc
 ret
psp_ok:
 mov ah,0x62
 int 0x21
 cmp bx,[terminal_trap_owner]
 jne .bad
 clc
 ret
.bad:
 stc
 ret
; Compare current vectors with ours (DX=0), baseline (DX=1), or either (DX=2).
vectors_ok:
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov si,indices
 mov di,terminal_trap_originals
 mov cx,3
.next:
 mov bx,[cs:si]
 cmp dx,1
 je .baseline
 mov ax,terminal_trap_break
 cmp cx,1
 jne .ours
 mov ax,terminal_trap_critical
.ours:
 cmp [es:bx],ax
 jne .not_ours
 mov ax,cs
 cmp [es:bx+2],ax
 je .matched
.not_ours:
 cmp dx,0
 je .bad
.baseline:
 mov ax,[di]
 cmp [es:bx],ax
 jne .bad
 mov ax,[di+2]
 cmp [es:bx+2],ax
 jne .bad
.matched:
 add si,2
 add di,4
 loop .next
 popf
 clc
 ret
.bad:
 popf
 stc
 ret
; Atomic three-vector installation/restoration, no DOS reentrancy window.
; AX=0 ours, AX=1 baseline. Phase is published by the caller first.
write_vectors:
 pushf
 cli
 mov dx,ax
 xor ax,ax
 mov es,ax
 mov si,indices
 mov di,terminal_trap_originals
 mov cx,3
.next:
 mov bx,[cs:si]
 or dx,dx
 jnz .baseline
 mov ax,terminal_trap_break
 cmp cx,1
 jne .handler
 mov ax,terminal_trap_critical
.handler:
 mov [es:bx],ax
 mov ax,cs
 jmp short .segment
.baseline:
 mov ax,[di]
 mov [es:bx],ax
 mov ax,[di+2]
.segment:
 mov [es:bx+2],ax
 add si,2
 add di,4
 loop .next
 popf
 ret
restore_flag:
 mov dx,[terminal_trap_flag]
 jmp short set_flag
parent_flag:
 xor dx,dx
set_flag:
 push dx
 mov ax,0x3301
 int 0x21
 mov ax,0x3300
 int 0x21
 xor dh,dh
 pop ax
 cmp dx,ax
 jne .bad
 clc
 ret
.bad:
 stc
 ret
failure:
 mov word [terminal_trap_phase],4
failed_admission:
 mov word [terminal_quit],1
 cmp word [terminal_exit_code],0
 jne .result
 mov word [terminal_exit_code],16
.result:
 mov ax,1
 ret
terminal_trap_open:
 save
 call context
 jc .invalid_context
 cmp word [terminal_trap_phase],0
 jne .failed
 mov ah,0x30
 int 0x21
 cmp al,3
 jb .failed
 mov ah,0x62
 int 0x21
 cmp bx,[process_psp]
 jne .failed
 mov [terminal_trap_owner],bx
 mov ax,0x3300
 int 0x21
 xor dh,dh
 cmp dx,1
 ja .failed
 mov [terminal_trap_flag],dx
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov si,indices
 mov di,terminal_trap_originals
 mov cx,3
.snapshot:
 mov bx,[cs:si]
 mov ax,cs
 cmp [es:bx+2],ax
 jne .capture
 mov ax,terminal_trap_break
 cmp cx,1
 jne .self_check
 mov ax,terminal_trap_critical
.self_check:
 cmp [es:bx],ax
 je .self_baseline
.capture:
 mov ax,[es:bx]
 mov [di],ax
 mov ax,[es:bx+2]
 mov [di+2],ax
 add si,2
 add di,4
 loop .snapshot
 mov word [terminal_trap_phase],3
 xor ax,ax
 call write_vectors
 popf
 call parent_flag
 jc .owned_failure
 mov word [terminal_trap_phase],1
 xor ax,ax
 restore
.self_baseline:
 popf
 call failed_admission
 restore
.owned_failure:
 call failure
 restore
.failed:
 call failed_admission
 restore
.invalid_context:
 mov ax,1
 restore
terminal_trap_suspend:
 save
 call context
 jc .invalid_context
 cmp word [terminal_trap_phase],1
 jne .failed
 xor dx,dx
 call vectors_ok
 jc .failed
 call psp_ok
 jc .failed
 call restore_flag
 jc .failed
 pushf
 cli
 cmp word [terminal_trap_pending],0
 jne .cancelled
 mov word [terminal_trap_phase],3
 mov ax,1
 call write_vectors
 mov word [terminal_trap_child],1
 mov word [terminal_trap_phase],2
 popf
 xor ax,ax
 restore
.cancelled:
 popf
 call failed_admission
 restore
.failed:
 call failure
 restore
.invalid_context:
 mov ax,1
 restore
terminal_trap_resume:
 save
 ; DOS2-style EXEC can return IF0/foreign context. The backend first restores
 ; the parent DS/SS/SP under CLI; install our handlers before enabling IRQs or
 ; making any DOS call that could otherwise reach the child's stale vector.
 call segments
 jc .invalid_context
 cmp word [terminal_trap_child],1
 jne .failed
 pushf
 cli
 mov word [terminal_trap_phase],3
 xor ax,ax
 call write_vectors
 mov word [terminal_trap_child],0
 popf
 sti
 mov bx,[terminal_trap_owner]
 mov ah,0x50
 int 0x21
 call psp_ok
 jc .failed
 call parent_flag
 jc .failed
 mov word [terminal_trap_phase],1
 xor ax,ax
 restore
.failed:
 call failure
 restore
.invalid_context:
 mov ax,1
 restore
terminal_trap_close:
 save
 call context
 jc .invalid_context
 cmp word [terminal_trap_phase],0
 je .closed
 cmp word [terminal_trap_child],1
 jne .validate
 mov word [terminal_trap_phase],3
 xor ax,ax
 call write_vectors
 jmp short .psp
.validate:
 mov dx,2
 call vectors_ok
 jc .failed
.psp:
 call psp_ok
 jc .failed
.recover:
 mov word [terminal_trap_phase],3
 xor ax,ax
 call write_vectors
 call restore_flag
 jc .failed
 mov ax,1
 call write_vectors
 mov word [terminal_trap_child],0
 mov word [terminal_trap_phase],0
.closed:
 call far terminal_trap_poll
 xor ax,ax
 restore
.failed:
 call failure
 restore
.invalid_context:
 mov ax,1
 restore
terminal_trap_poll:
 pushf
 push ax
 push ds
 mov ax,DGROUP
 mov ds,ax
 cmp word [terminal_trap_phase],2
 je .done
 cmp word [terminal_trap_pending],0
 je .done
 mov word [terminal_quit],1
 cmp word [terminal_exit_code],0
 jne .done
 mov word [terminal_exit_code],16
.done:
 pop ds
 pop ax
 popf
 retf
terminal_trap_break:
 push ax
 push ds
 mov ax,DGROUP
 mov ds,ax
 or word [terminal_trap_pending],1
 pop ds
 pop ax
 iret
terminal_trap_critical:
 push ds
 push bx
 mov bx,DGROUP
 mov ds,bx
 mov [terminal_trap_error_context],ax
 mov [terminal_trap_error_code],di
 or word [terminal_trap_pending],2
 test ah,8 ; DOS3+ permits Fail; otherwise Fail would become Abort.
 jz terminal_trap_hold
 mov al,3
 pop bx
 pop ds
 iret
terminal_trap_hold:
 sti
 hlt
 jmp terminal_trap_hold
indices: dw 0x1b*4,0x23*4,0x24*4
SEGMENT _DATA public class=DATA use16
global terminal_trap_phase,terminal_trap_pending,terminal_trap_owner,terminal_trap_originals
global terminal_trap_flag,terminal_trap_child,terminal_trap_error_context,terminal_trap_error_code
terminal_trap_phase: dw 0
terminal_trap_pending: dw 0
terminal_trap_owner: dw 0
terminal_trap_flag: dw 0
terminal_trap_child: dw 0
terminal_trap_originals: times 6 dw 0
terminal_trap_error_context: dw 0
terminal_trap_error_code: dw 0
%endif
