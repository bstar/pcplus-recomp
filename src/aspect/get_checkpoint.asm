; Maintained near checkpoint around recovered interactive GET. This is a
; lifetime adapter, not recovered original bytes. Error identity lives in the
; runtime; this layer never changes it or commits a destination after abort.
BITS 16
CPU 8086
%ifdef GET_RESIDENT_CHECKPOINT
 %define GET_STATE_SEG ss
%else
 %define GET_STATE_SEG cs
%endif
SEGMENT _TEXT public class=CODE use16
extern aspect_get,aspect_abort_recovered
%ifdef ASPECT_ALARM_VM
 extern runtime_alarm_abort_gate
%endif
global _runtime_get_native,_runtime_get_native_active
global _runtime_get_native_aborted,_runtime_get_native_generation,runtime_get_abort_gate
_runtime_get_native_generation:
 mov ax,[GET_STATE_SEG:get_generation]
 ret
_runtime_get_native_active:
 mov ax,[GET_STATE_SEG:get_checkpoint]
 ret
_runtime_get_native_aborted:
 mov ax,[GET_STATE_SEG:get_aborted]
 ret
_runtime_get_native:
%ifdef GET_RESIDENT_CHECKPOINT
 ; Check the actual resident data stack before using SS-relative state.
 ; Unlike overlaid CS, SS remains valid when a native fault changes DS.
 mov ax,ss
 mov dx,DGROUP
 cmp ax,dx
 jne .context
%endif
 cmp word [GET_STATE_SEG:get_checkpoint],0
 jne .busy
 ; Do not arm a checkpoint on a foreign data stack or with IF disabled.
 push ds
 pop ax
 push ss
 pop dx
 cmp ax,dx
 jne .context
 pushf
 pop ax
 test ax,0x0200
 jz .context
 test ax,0x0400
 jnz .context
 push bp
 push si
 push di
 push bx
 push es
 mov [GET_STATE_SEG:get_saved_ss],ss
 mov [GET_STATE_SEG:get_saved_sp],sp
 ; Capture flags after entry guards. The C ABI does not promise incoming
 ; arithmetic flags; preserve this exact foreground IF/DF state on abort.
 pushf
 pop word [GET_STATE_SEG:get_saved_flags]
 inc word [GET_STATE_SEG:get_generation]
 jnz .generation_ready
 inc word [GET_STATE_SEG:get_generation]
.generation_ready:
 mov word [GET_STATE_SEG:get_aborted],0
 mov word [GET_STATE_SEG:get_checkpoint],1
%ifdef ASPECT_GET_CONTEXT
 extern _runtime_get_context_enter,_runtime_get_context_leave
 call _runtime_get_context_enter
 or ax,ax
 jnz runtime_get_abort_gate
%endif
 call aspect_get
%ifdef ASPECT_GET_CONTEXT
 call _runtime_get_context_leave
 or ax,ax
 jnz runtime_get_abort_gate
%endif
 mov word [GET_STATE_SEG:get_checkpoint],0
.return:
 pop es
 pop bx
 pop di
 pop si
 pop bp
 mov word [GET_STATE_SEG:get_saved_ss],0
 mov word [GET_STATE_SEG:get_saved_sp],0
 mov word [GET_STATE_SEG:get_saved_flags],0
 mov ax,[GET_STATE_SEG:get_aborted]
 ret
.busy:
 mov ax,2
 ret
.context:
 mov ax,3
 ret
runtime_get_abort_gate:
 cmp word [GET_STATE_SEG:get_checkpoint],1
 jne .fallback
 mov ax,ss
 cmp ax,[GET_STATE_SEG:get_saved_ss]
 jne .fallback
 cli
 mov ax,[GET_STATE_SEG:get_saved_ss]
 mov ss,ax
 mov sp,[GET_STATE_SEG:get_saved_sp]
 mov ds,ax
 mov word [GET_STATE_SEG:get_checkpoint],0
 mov word [GET_STATE_SEG:get_aborted],1
 push word [GET_STATE_SEG:get_saved_flags]
 popf
 jmp _runtime_get_native.return
.fallback:
%ifdef ASPECT_ALARM_VM
 jmp runtime_alarm_abort_gate
%else
 jmp aspect_abort_recovered
%endif
%ifdef GET_RESIDENT_CHECKPOINT
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global get_resident_checkpoint_state
get_resident_checkpoint_state:
%endif
get_saved_ss: dw 0
get_saved_sp: dw 0
get_saved_flags: dw 0
get_checkpoint: dw 0
get_aborted: dw 0
get_generation: dw 0
