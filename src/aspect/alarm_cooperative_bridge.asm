; C adapters around the exact native alert's RET2/RET4 service conventions.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_alarm_alert
extern _alarm_coop_seconds,_alarm_coop_peek,_alarm_coop_read
extern _alarm_coop_ticks,_alarm_coop_tone
global _alarm_coop_native,alarm_seconds,alarm_peek,alarm_read
global alarm_ticks,alarm_tone,alarm_option,alarm_operand
%ifdef ASPECT_ALARM_VM
extern aspect_abort_recovered
global runtime_alarm_abort_gate,_alarm_coop_native_aborted
; Native service errors use a nonreturning VM abort. Catch only this owner's
; stack, return to its C caller, then let ordinary tone/WHEN cleanup run before
; the wrapper restores duration and propagates the original typed error.
_alarm_coop_native:
 push bp
 push si
 push di
 push es
 mov [cs:alarm_saved_ss],ss
 mov [cs:alarm_saved_sp],sp
 pushf
 pop word [cs:alarm_saved_flags]
 mov word [cs:alarm_aborted],0
 mov word [cs:alarm_checkpoint],1
 call aspect_alarm_alert
 mov word [cs:alarm_checkpoint],0
.return:
 pop es
 pop di
 pop si
 pop bp
 ret
runtime_alarm_abort_gate:
 cmp word [cs:alarm_checkpoint],1
 jne aspect_abort_recovered
 mov ax,ss
 cmp ax,[cs:alarm_saved_ss]
 jne aspect_abort_recovered
 cli
 mov ax,[cs:alarm_saved_ss]
 mov ss,ax
 mov sp,[cs:alarm_saved_sp]
 mov ds,ax
 mov es,ax
 mov word [cs:alarm_checkpoint],0
 mov word [cs:alarm_aborted],1
 push word [cs:alarm_saved_flags]
 popf
 jmp _alarm_coop_native.return
_alarm_coop_native_aborted:
 mov ax,[cs:alarm_aborted]
 ret
alarm_saved_ss: dw 0
alarm_saved_sp: dw 0
alarm_saved_flags: dw 0
alarm_checkpoint: dw 0
alarm_aborted: dw 0
%else
_alarm_coop_native: jmp aspect_alarm_alert
%endif
alarm_seconds: jmp _alarm_coop_seconds
alarm_peek: jmp _alarm_coop_peek
alarm_read: jmp _alarm_coop_read
%ifdef ASPECT_ALARM_VM
extern aspect_string_option_flag,aspect_console_pause_operand
alarm_option: jmp aspect_string_option_flag
alarm_operand: jmp aspect_console_pause_operand
%else
; The standalone component calls the alert, not the ASPECT operand wrapper.
alarm_option:
alarm_operand:
 xor ax,ax
 ret
%endif
alarm_ticks:
 push bp
 mov bp,sp
 push word [bp+4]
 call _alarm_coop_ticks
 add sp,2
 pop bp
 ret 2
alarm_tone:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _alarm_coop_tone
 add sp,4
 pop bp
 ret 4
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
global alarm_duration,alarm_enabled
alarm_duration: dw 0
alarm_enabled: dw 0
