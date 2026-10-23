BITS 16
CPU 8086
%ifdef TERMINAL_HOOK_INPUT
SEGMENT _TEXT public class=CODE use16
extern terminal_setup_profile_stage
global hook_input_profile_resident
hook_input_profile_resident:
 call terminal_setup_profile_stage
 retf
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global _hook_profile_stage
_hook_profile_stage:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 call far hook_input_profile_resident
 pop bp
 retf
global _terminal_hook_input_offer,_terminal_hook_input_bound
_terminal_hook_input_bound: dw 0
_terminal_hook_input_offer: times 1212 db 0
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%macro entry 3
 extern %2
 global %1
 %1:
 push bp
 mov bp,sp
 %assign arg %3-1
 %rep %3
 push word [bp+6+2*arg]
 %assign arg arg-1
 %endrep
 call %2
 mov sp,bp
 pop bp
 retf
%endmacro
entry _hook_xlt_bind,_xlt_live_bind_impl,1
entry _hook_xlt_stage,_xlt_live_stage_impl,2
entry _hook_xlt_offer,_xlt_live_offer_impl,2
%endif
