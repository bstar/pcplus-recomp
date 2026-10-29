; Maintained bounded DOS EXEC boundary. DS=SS; near caller removes6 bytes.
; The recovered vendor executor is separately retained in program_exec.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global process_run,_process_run
%ifdef PROCESS_CODE_BANK
; Both public names retain the original near three-word caller-cleaned ABI.
process_run:
_process_run:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far process_run_far
 lea sp,[bp]
 pop bp
 ret
SEGMENT PROCESS_CODE public align=16 class=FARCODE use16
GROUP PROCESS_GROUP PROCESS_CODE
global terminal_process_code_start,terminal_process_code_end
global process_run_far,process_run_impl
global process_string_length,process_result_disjoint,process_owned_disjoint
global process_saved_ds,process_saved_ss,process_saved_sp,process_exec_ax,process_exec_failed
terminal_process_code_start:
process_run_far:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call process_run_impl
 lea sp,[bp]
 pop bp
 retf
%endif

; (path ASCIIZ1..127, or1..259 with PROCESS_LONG_PATHS; optional tail0..126/result8).
; AX0 child ran;1 invalid arguments/state;2 resize failure;3 EXEC failure;4 busy.
; Result WORDs: status,DOS error,child termination/exit AX,retained paragraphs.
; Invalid arguments/busy leave result unchanged. Preserve BP/SI/DI/DS/ES/SS/SP.
%ifdef PROCESS_CODE_BANK
process_run_impl:
%else
process_run:
_process_run:
%endif
 push bp
 mov bp,sp
 push si
 push di
 push es
 cmp word [process_busy],0
 jne .busy
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 extern mouse_allocation_strategy_held
 cmp word [process_loan_restore_error],0
 jne .busy
 cmp word [mouse_allocation_strategy_held],0
 jne .busy
%endif
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .invalid
 cmp word [process_psp],0
 je .invalid
 cmp word [process_keep_paragraphs],0x10
 jb .invalid
 cmp word [process_minimum_paragraphs],0x10
 jb .invalid
 mov ax,[process_keep_paragraphs]
 cmp ax,[process_minimum_paragraphs]
 jb .invalid
 mov si,[bp+4]
 or si,si
 jz .invalid
%ifdef PROCESS_LONG_PATHS
 mov ax,259
%else
 mov ax,127
%endif
 call process_string_length
 jc .invalid
 or cx,cx
 jz .invalid
 mov [process_path_length],cx
 mov ax,[bp+4]
 inc cx
 call process_owned_disjoint
 jc .invalid
 mov si,[bp+6]
 xor cx,cx
 or si,si
 jz .tail_valid
 mov ax,126
 call process_string_length
 jc .invalid
.tail_valid:
 mov [process_tail_length],cx
 mov ax,[bp+6]
 or ax,ax
 jz .result_pointer
 inc cx
 call process_owned_disjoint
 jc .invalid
.result_pointer:
 mov dx,[bp+8]
 or dx,dx
 jz .validated
 cmp dx,0xfff8
 ja .invalid
 mov ax,dx
 mov cx,8
 call process_owned_disjoint
 jc .invalid
 mov ax,[bp+4]
 mov cx,[process_path_length]
 inc cx
 call process_result_disjoint
 jc .invalid
 mov ax,[bp+6]
 or ax,ax
 jz .validated
 mov cx,[process_tail_length]
 inc cx
 call process_result_disjoint
 jc .invalid
.validated:
%ifdef TERMINAL_DIRECTORY_STORAGE
 extern _directory_storage_exec_allowed
 call far _directory_storage_exec_allowed
 or ax,ax
 jz .busy
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 extern _directory_resources_exec_allowed
 call far _directory_resources_exec_allowed
 or ax,ax
 jz .busy
%endif
%endif
 mov word [process_busy],1
 mov word [process_status],0
 mov word [process_dos_error],0
 mov word [process_child_status],0
 mov ax,[bp+4]
 mov [process_path],ax
 mov ax,[bp+8]
 mov [process_result],ax
 ; Construct a DOS command tail, including the explicit length and final CR.
 push ds
 pop es
 cld
 xor ax,ax
 mov di,process_command_tail
 mov cx,64
 rep stosw
 mov di,process_fcb1
 mov cx,37
 rep stosw
 mov ax,[process_tail_length]
 mov [process_command_tail],al
 mov cx,ax
 mov si,[bp+6]
 mov di,process_command_tail+1
 rep movsb
 mov byte [di],13
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 global process_loan_begin_site
 process_loan_begin_site equ $
 call process_loan_begin
%endif
 cmp word [process_memory_released],0
 jne .execute
 mov es,[process_psp]
 mov bx,[process_keep_paragraphs]
 mov ah,0x4a
 int 0x21
 jnc .resized
 mov [process_dos_error],ax
 mov word [process_status],2
 jmp .finish
.resized:
 mov word [process_memory_released],1
.execute:
 push ds
 pop es
 mov si,process_command_tail+1
 mov di,process_fcb1
 mov ax,0x2901
 int 0x21
 mov di,process_fcb2
 mov ax,0x2901
 int 0x21
 mov word [process_parameters],0 ; DOS inherits the parent's environment.
 mov word [process_parameters+2],process_command_tail
 mov word [process_parameters+4],ds
 mov word [process_parameters+6],process_fcb1
 mov word [process_parameters+8],ds
 mov word [process_parameters+10],process_fcb2
 mov word [process_parameters+12],ds
 mov bx,process_parameters
 mov dx,[process_path]
%ifdef TERMINAL_TRAPS
 extern terminal_trap_suspend,terminal_trap_resume
 call far terminal_trap_suspend
 or ax,ax
 jnz .trap_failed
%endif
 mov [cs:process_saved_ds],ds
 mov [cs:process_saved_ss],ss
 mov [cs:process_saved_sp],sp
 mov ax,0x4b00
 int 0x21
 ; Do not use DS or the returned stack before restoring the parent's context.
 mov [cs:process_exec_ax],ax
 mov byte [cs:process_exec_failed],0
 jnc .context
 mov byte [cs:process_exec_failed],1
.context:
 cli
 mov ss,[cs:process_saved_ss]
 mov sp,[cs:process_saved_sp]
 mov ds,[cs:process_saved_ds]
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 extern terminal_process_quiet_uart
 global process_child_quiet_site
 process_child_quiet_site equ $
 call far terminal_process_quiet_uart
%endif
%ifdef TERMINAL_TRAPS
 call far terminal_trap_resume
 or ax,ax
 jnz .trap_failed
%endif
 sti
 cmp byte [cs:process_exec_failed],0
 je .child_returned
 mov ax,[cs:process_exec_ax]
 mov [process_dos_error],ax
 mov word [process_status],3
 jmp .finish
.child_returned:
 mov ah,0x4d
 int 0x21
 mov [process_child_status],ax
.finish:
%ifdef TERMINAL_TRAPS
 jmp short .result
.trap_failed:
 mov word [process_status],7
.result:
%endif
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 global process_loan_end_site
 process_loan_end_site equ $
 call process_loan_end
%endif
 mov di,[process_result]
 or di,di
 jz .status
 push ds
 pop es
 mov si,process_status
 mov cx,3
 cld
 rep movsw
 mov ax,[process_keep_paragraphs]
 stosw
.status:
 mov word [process_busy],0
 mov ax,[process_status]
 jmp .done
.invalid:
 mov ax,1
 jmp .done
.busy:
 mov ax,4
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
; The frozen snapshot/index is the final allocation. It is rebuilt from the
; separately retained live ring at the next view, and has no active consumer
; across these explicit PROGRAM/owner gates. Never lend for resource kind6.
extern terminal_program_pending,terminal_program_active,terminal_program_kind
extern _redisplay_active,_command_menu_active,_redisplay_live_ready,terminal_snapshot_active
extern terminal_program_critical_paragraphs,terminal_quit,terminal_exit_code
global process_loan_begin,process_loan_end
process_loan_begin:
 mov word [process_loan_active],0
 cmp word [terminal_program_active],1
 jne .done
 mov ax,[terminal_program_kind]
 cmp ax,5
 ja .done
 cmp ax,2
 je .done
 mov ax,[terminal_program_pending]
 or ax,[_redisplay_active]
 or ax,[_command_menu_active]
 or ax,[_redisplay_live_ready]
 or ax,[terminal_snapshot_active]
 jnz .done
 mov ax,[process_keep_paragraphs]
 cmp ax,[process_minimum_paragraphs]
 jne .done
 mov dx,[terminal_program_critical_paragraphs]
 cmp dx,10h
 jb .done
 cmp dx,ax
 jae .done
 mov [process_loan_full],ax
 mov [process_keep_paragraphs],dx
 mov [process_minimum_paragraphs],dx
 mov word [process_loan_active],1
 mov word [process_memory_released],0 ;Every loan must actually resize again.
.done:
 ret
process_loan_end:
 cmp word [process_loan_active],1
 jne .done
 mov es,[process_psp]
 mov bx,[process_loan_full]
 mov ah,4ah
 int 21h
 jc .failed
 mov ax,[process_loan_full]
 mov [process_keep_paragraphs],ax
 mov [process_minimum_paragraphs],ax
 mov word [process_loan_active],0
 mov word [process_memory_released],1
 ret
.failed:
 mov [process_loan_restore_error],ax
 cmp word [process_dos_error],0
 jne .primary
 mov [process_dos_error],ax
.primary:
 mov ax,[process_loan_full]
 mov [process_minimum_paragraphs],ax
 ; Keep reflects the smaller actual block, never falsely report reacquisition.
 mov word [process_status],8
 mov word [process_loan_active],0
 mov word [terminal_quit],1
 cmp word [terminal_exit_code],0
 jne .done
 mov word [terminal_exit_code],7
.done:
 ret
%endif

; DS:SI ASCIIZ, AX max payload. CX payload length, CF1 invalid/wrapped.
; Reject CR/LF: an internal CR must not silently truncate a DOS command tail.
process_string_length:
 xor cx,cx
.next:
 cmp byte [si],0
 je .valid
 cmp byte [si],13
 je .invalid
 cmp byte [si],10
 je .invalid
 cmp cx,ax
 jae .invalid
 inc si
 jz .invalid
 inc cx
 jmp .next
.valid:
 clc
 ret
.invalid:
 stc
 ret

; AX start,CX extent,DX result8; CF1 overlap, including a result ending10000h.
process_result_disjoint:
 mov bx,dx
 cmp dx,ax
 jae .result_after
 sub ax,dx
 cmp ax,8
 jb .overlap
 clc
 ret
.result_after:
 sub bx,ax
 cmp bx,cx
 jb .overlap
 clc
 ret
.overlap:
 stc
 ret

; Reject any caller region overlapping this nonreentrant backend's own state.
process_owned_disjoint:
 cmp ax,process_owned_end
 jae .valid
 mov bx,process_owned_start
 cmp ax,bx
 jae .invalid
 sub bx,ax
 cmp cx,bx
 ja .invalid
.valid:
 clc
 ret
.invalid:
 stc
 ret

; DOS2 EXEC may return a changed stack; these are deliberately CS-relative.
process_saved_ds: dw 0
process_saved_ss: dw 0
process_saved_sp: dw 0
process_exec_ax: dw 0
process_exec_failed: db 0
%ifdef PROCESS_CODE_BANK
terminal_process_code_end:
%endif

SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
global process_psp,process_keep_paragraphs,process_minimum_paragraphs,process_memory_released,process_busy
global _process_psp
global process_status,process_dos_error,process_child_status
global process_command_tail,process_parameters,process_fcb1,process_fcb2
process_owned_start:
process_psp:
_process_psp: dw 0
process_keep_paragraphs: dw 0
process_minimum_paragraphs: dw 0
process_memory_released: dw 0
process_busy: dw 0
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
global process_loan_active,process_loan_full,process_loan_restore_error
process_loan_active: dw 0
process_loan_full: dw 0
process_loan_restore_error: dw 0
%endif
; Keep the three result WORDs contiguous.
process_status: dw 0
process_dos_error: dw 0
process_child_status: dw 0
process_path: dw 0
process_result: dw 0
process_path_length: dw 0
process_tail_length: dw 0
process_command_tail: times 128 db 0
process_parameters: times 14 db 0
process_fcb1: times 37 db 0
process_fcb2: times 37 db 0
process_owned_end:
