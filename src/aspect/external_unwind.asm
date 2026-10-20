; Near DS=SS checkpoint. The recovered VM abort remains the final unwind.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _runtime_external_execute_inner,_runtime_external_recover
extern runtime_divide_original,aspect_abort_recovered,aspect_abort
global _runtime_external_execute,_runtime_external_checkpoint_active
global _runtime_external_checkpoint_retire
global _runtime_external_checkpoint_recovering
global runtime_external_abort_gate,runtime_external_divide_gate,native_external_divide_gate
_runtime_external_checkpoint_active:
 mov ax,[cs:checkpoint_ready]
 ret
_runtime_external_checkpoint_retire:
 mov word [cs:checkpoint_ready],0
 ret
_runtime_external_checkpoint_recovering:
 mov word [cs:checkpoint_ready],2
 ret
_runtime_external_execute:
 cmp word [cs:checkpoint_ready],0
 jne .busy
 mov [cs:checkpoint_ss],ss
 mov [cs:checkpoint_sp],sp
 pushf
 pop word [cs:checkpoint_flags]
 mov word [cs:checkpoint_ready],1
 push bp
 mov bp,sp
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _runtime_external_execute_inner
 add sp,10
 pop bp
 mov word [cs:checkpoint_ready],0
 ret
.busy:
 ; A nested request may not overwrite the live recovery point.
 extern _runtime_set_error
 mov ax,10
 push ax
 call _runtime_set_error
 add sp,2
 mov ax,0xffff
 ret
runtime_external_abort_gate:
 cmp word [cs:checkpoint_ready],1
 jne aspect_abort_recovered
 mov word [cs:checkpoint_cause],0 ; retain the actual typed runtime error
 jmp checkpoint_fault
runtime_external_divide_gate:
 cmp word [cs:checkpoint_ready],1
 jne runtime_divide_original
 jmp parent_divide
native_external_divide_gate:
 cmp word [cs:checkpoint_ready],1
 jne child_divide
parent_divide:
 push bp
 mov bp,sp
 push ax
 mov ax,ss
 cmp ax,[cs:checkpoint_ss]
 jne .foreign
 mov word [cs:checkpoint_cause],12
 mov word [ss:bp+2],checkpoint_fault
 mov word [ss:bp+4],cs
 pop ax
 pop bp
 iret
.foreign:
 pop ax
 pop bp
child_divide:
 ; A real DOS child owns a different stack/allocation, even with foreign DS.
 ; It must never jump into its waiting parent's saved near context.
 mov ax,0x4c0c
 sti
 int 0x21
checkpoint_fault:
 cli
 mov ax,[cs:checkpoint_ss]
 mov ss,ax
 mov sp,[cs:checkpoint_sp]
 ; The entry ABI is DS=SS; the saved stack segment owns both contexts.
 mov ds,ax
 mov es,ax
 ; Cleanup needs a valid C stack, not the interrupted C register values.
 ; The recovered dispatcher longjmp below restores its own BP/SI/DI context.
 mov word [cs:checkpoint_ready],2
 push word [cs:checkpoint_flags]
 popf
 cld
 push word [cs:checkpoint_cause]
 call _runtime_external_recover
 add sp,2
 ; The outer runtime entry owns the caller's original ES. Cleanup continues
 ; in the data segment until its recovered dispatcher restores that frame.
 push ds
 pop es
 mov word [cs:checkpoint_ready],0
 jmp aspect_abort_recovered
%ifdef ASPECT_EXTERNAL_DIAGNOSTIC
global _runtime_external_raise
global _runtime_external_phase
extern _runtime_external_fault_kind
extern _runtime_external_fault_at,_runtime_external_fault_fired
extern _runtime_external_arena_copy,_runtime_external_arena_valid
extern _runtime_external_arena_changed,_runtime_external_frame_offset
extern _runtime_arena,_runtime_frame
; Keep test instrumentation out of the C controller's register assumptions.
; This independent8086 copy supplies the baseline checked by C _fmemcmp after
; recovery. Both allocations are bounded single-segment objects of15050 bytes.
_runtime_external_phase:
 push bp
 mov bp,sp
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cmp word [cs:checkpoint_ready],1
 jne .done
 mov bx,[bp+4]
 cmp bx,1
 jne .arena
 mov ax,[_runtime_external_arena_copy+2]
 or ax,[_runtime_external_arena_copy]
 jz .arena
 les di,[_runtime_external_arena_copy]
 mov si,_runtime_arena
 mov cx,0x3aca
 cld
 rep movsb
 mov word [_runtime_external_arena_valid],1
 mov ax,[_runtime_frame]
 sub ax,_runtime_arena
 mov [_runtime_external_frame_offset],ax
.arena:
 cmp bx,9
 jne .trigger
 cmp word [_runtime_external_arena_valid],0
 je .trigger
 les di,[_runtime_external_arena_copy]
 mov si,_runtime_arena
 mov cx,0x3aca
 cld
 repe cmpsb
 mov ax,0
 je .same
 inc ax
.same:
 mov [_runtime_external_arena_changed],ax
.trigger:
 cmp bx,[_runtime_external_fault_at]
 jne .done
 mov word [_runtime_external_fault_at],0
 inc word [_runtime_external_fault_fired]
 call _runtime_external_raise
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 pop bp
 ret
_runtime_external_raise:
 test word [_runtime_external_fault_kind],1
 jnz .typed
 cmp word [_runtime_external_fault_kind],2
 jne .divide
 mov ax,0x40
 mov ds,ax
.divide:
 mov ax,1
 xor dx,dx
 xor bx,bx
 div bx ; real INT0, never an emulated successful recovery return
 ret
.typed:
 mov ax,5
 push ax
 call _runtime_set_error
 add sp,2
 cmp word [_runtime_external_fault_kind],3
 jne aspect_abort
 extern aspect_dispatch_exit_state,aspect_dispatch_argument,session_longjmp
 mov ax,0xffff
 mov [aspect_dispatch_exit_state],ax
 push ax
 mov ax,aspect_dispatch_argument
 push ax
 call session_longjmp ; deliberately bypass the checkpoint's abort gate
%endif
checkpoint_ready: dw 0
checkpoint_ss: dw 0
checkpoint_sp: dw 0
checkpoint_flags: dw 0
checkpoint_cause: dw 0
