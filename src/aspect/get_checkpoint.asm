; Maintained near checkpoint around recovered interactive GET. This is a
; lifetime adapter, not recovered original bytes. Error identity lives in the
; runtime; this layer never changes it or commits a destination after abort.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_get,aspect_abort_recovered
%ifdef ASPECT_ALARM_VM
 extern runtime_alarm_abort_gate
%endif
global _runtime_get_native,_runtime_get_native_active
global _runtime_get_native_aborted,runtime_get_abort_gate
_runtime_get_native_active:
 mov ax,[cs:get_checkpoint]
 ret
_runtime_get_native_aborted:
 mov ax,[cs:get_aborted]
 ret
_runtime_get_native:
 cmp word [cs:get_checkpoint],0
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
 mov [cs:get_saved_ss],ss
 mov [cs:get_saved_sp],sp
 ; Capture flags after entry guards. The C ABI does not promise incoming
 ; arithmetic flags; preserve this exact foreground IF/DF state on abort.
 pushf
 pop word [cs:get_saved_flags]
 mov word [cs:get_aborted],0
 mov word [cs:get_checkpoint],1
 call aspect_get
 mov word [cs:get_checkpoint],0
.return:
 pop es
 pop bx
 pop di
 pop si
 pop bp
 mov word [cs:get_saved_ss],0
 mov word [cs:get_saved_sp],0
 mov word [cs:get_saved_flags],0
 mov ax,[cs:get_aborted]
 ret
.busy:
 mov ax,2
 ret
.context:
 mov ax,3
 ret
runtime_get_abort_gate:
 cmp word [cs:get_checkpoint],1
 jne .fallback
 mov ax,ss
 cmp ax,[cs:get_saved_ss]
 jne .fallback
 cli
 mov ax,[cs:get_saved_ss]
 mov ss,ax
 mov sp,[cs:get_saved_sp]
 mov ds,ax
 mov word [cs:get_checkpoint],0
 mov word [cs:get_aborted],1
 push word [cs:get_saved_flags]
 popf
 jmp _runtime_get_native.return
.fallback:
%ifdef ASPECT_ALARM_VM
 jmp runtime_alarm_abort_gate
%else
 jmp aspect_abort_recovered
%endif
get_saved_ss: dw 0
get_saved_sp: dw 0
get_saved_flags: dw 0
get_checkpoint: dw 0
get_aborted: dw 0
