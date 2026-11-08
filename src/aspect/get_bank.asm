; Explicit ordinary DS=SS near-cdecl <-> GET_VM_CODE adapters. GET's native
; checkpoint restores a stack within this bank; only the final dispatcher abort
; crosses back to resident CS before the original near longjmp.
BITS 16
CPU 8086
%macro GET_ENTRY 2
 %ifdef GET_BANK_ROOT_ONLY
 extern %1 %+ _far
 %endif
 global %1
 %1:
 %if %2=0
 call far %1 %+ _far
 ret
 %else
 push bp
 mov bp,sp
 %assign %%i %2-1
 %rep %2
 push word [bp+4+2*%%i]
 %assign %%i %%i-1
 %endrep
 call far %1 %+ _far
 mov sp,bp
 pop bp
 ret
 %endif
%endmacro
%macro GET_CALLBACK 3
 extern %2
 global %1 %+ _resident
 %1 %+ _resident:
 %if %3=0
 call %2
 retf
 %else
 push bp
 mov bp,sp
 %assign %%i %3-1
 %rep %3
 push word [bp+8+2*%%i]
 %assign %%i %%i-1
 %endrep
 call %2
 mov sp,bp
 pop bp
 retf
 %endif
%endmacro
%ifndef GET_BANK_OVERLAY_ONLY
SEGMENT _TEXT public class=CODE use16
%include "get_bank.inc"
extern runtime_get_abort_gate_impl,aspect_abort_recovered,runtime_alarm_abort_gate
global runtime_get_abort_gate
runtime_get_abort_gate: jmp far runtime_get_abort_gate_impl
global get_bank_abort_resident,get_bank_alarm_resident
get_bank_abort_resident: jmp aspect_abort_recovered
get_bank_alarm_resident: jmp runtime_alarm_abort_gate
%endif
%unmacro GET_ENTRY 2
%unmacro GET_CALLBACK 3
%macro GET_ENTRY 2
 extern %1 %+ _impl
 global %1 %+ _far
 %1 %+ _far:
 %if %2=0
 call %1 %+ _impl
 retf
 %else
 push bp
 mov bp,sp
 %assign %%i %2-1
 %rep %2
 push word [bp+6+2*%%i]
 %assign %%i %%i-1
 %endrep
 call %1 %+ _impl
 mov sp,bp
 pop bp
 retf
 %endif
%endmacro
%macro GET_CALLBACK 3
 %ifdef GET_BANK_OVERLAY_ONLY
 extern %1 %+ _resident
 %endif
 global %1
 %1:
 call far %1 %+ _resident
 ret
%endmacro
%ifndef GET_BANK_ROOT_ONLY
%ifdef GET_BANK_OVERLAY_ONLY
extern get_bank_abort_resident,get_bank_alarm_resident
%endif
SEGMENT GET_VM_CODE public align=16 class=FARCODE use16
%include "get_bank.inc"
global get_bank_abort,get_bank_alarm
get_bank_abort: jmp far get_bank_abort_resident
get_bank_alarm: jmp far get_bank_alarm_resident
%endif
