; Seven register-only callbacks and one explicit callee-cleaned stack callback.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%macro PHONE_ENTRY 2
%endmacro
%define PHONE_REGISTER NEAR_NAMED_SERVICE
%macro PHONE_STACK 2
 global %1 %+ _resident
 extern %2
 %1 %+ _resident:
 push bp
 mov bp,sp
 ; Saved BP, far return, near service return, original spilled WORD.
 push word [bp+8]
 call %2
 pop bp
 retf
%endmacro
%include "phone_log_abi.inc"
