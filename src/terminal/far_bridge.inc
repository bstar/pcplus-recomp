; Static real-mode code bridges. DS=SS is inherited and never changed.
; Only register/no-argument, plain RET services may cross these frames.
; CALL/RET/RETF preserve returned flags and register values. Not for RET N,
; C stack arguments, CS-relative assumptions or interrupt entry points.
%macro NEAR_ENTRY 1
 extern %1 %+ _far
 global %1
 %1:
 call far %1 %+ _far
 ret
%endmacro
%macro FAR_ENTRY 1
 global %1 %+ _far
 %1 %+ _far:
 call %1 %+ _impl
 retf
%endmacro
%macro NEAR_SERVICE 1
 extern %1
 global %1 %+ _resident
 %1 %+ _resident:
 call %1
 retf
%endmacro
%macro FAR_SERVICE 1
 global %1 %+ _service
 extern %1 %+ _resident
 %1 %+ _service:
 call far %1 %+ _resident
 ret
%endmacro

; Explicit adapter: caller supplies AX; target accepts one caller-cleaned word.
; Preserve AX and target flags with POP rather than arithmetic stack cleanup.
%macro NEAR_AX_STACK_SERVICE 1
 extern %1
 global %1 %+ _resident
 %1 %+ _resident:
 push ax
 call %1
 pop ax
 retf
%endmacro
