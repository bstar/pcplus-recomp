; Static real-mode code bridges. DS=SS is inherited and never changed.
; The basic entry/service macros below accept register/no-argument, plain RET
; interfaces. CALL/RET/RETF preserve returned flags and register values. They
; do not forward C stack arguments, RET N or interrupt frames. Explicit
; caller-cleaned word adapters are separately defined at the end of this file.
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

; Namespaced register service: multiple far modules may call the same resident
; function without sharing a thunk's CS or defining duplicate public symbols.
%macro NEAR_NAMED_SERVICE 2
 extern %2
 global %1 %+ _resident
 %1 %+ _resident:
 call %2
 retf
%endmacro
%macro FAR_NAMED_SERVICE 2
 FAR_SERVICE %1
%endmacro

; Explicit caller-cleaned word-argument service. The far caller first CALLs a
; near service thunk, which CALL FARs this resident adapter. Incoming args thus
; begin at BP+8 after saving BP. Copy1..4 words to a new ordinary near-C frame.
; LEA releases only those copies without changing returned flags/AX/DX/BX.
; Requires DS=SS and BP-preserving, plain-RET targets. No RET N, variadic
; arguments, callbacks or writes back into the caller's argument slots.
%macro NEAR_CDECL_SERVICE 3
 %if %3 < 1 || %3 > 4
  %error Only explicitly declared1..4-word cdecl services are supported
 %endif
 extern %2
 global %1 %+ _resident
 %1 %+ _resident:
 push bp
 mov bp,sp
 %assign %%argument %3-1
 %rep %3
  push word [bp+8+2*%%argument]
  %assign %%argument %%argument-1
 %endrep
 call %2
 lea sp,[bp]
 pop bp
 retf
%endmacro
%macro FAR_CDECL_SERVICE 3
 FAR_SERVICE %1
%endmacro

; Explicit near-cdecl -> far wrapper -> near-C implementation. Both wrappers
; copy only declared argument words, retaining DS=SS and caller-owned slots.
; Separate entry family supports these known1..9-word APIs; it does not change
; the modem callback family's1..4-word contract or accept variadic/RET N APIs.
%macro NEAR_CDECL_ENTRY 2
 %if %2 < 1 || %2 > 9
  %error Only explicitly declared1..9-word entries are supported
 %endif
 extern %1 %+ _far
 global %1
 %1:
 push bp
 mov bp,sp
 %assign %%argument %2-1
 %rep %2
  push word [bp+4+2*%%argument]
  %assign %%argument %%argument-1
 %endrep
 call far %1 %+ _far
 lea sp,[bp]
 pop bp
 ret
%endmacro
%macro FAR_CDECL_ENTRY 2
 %if %2 < 1 || %2 > 9
  %error Only explicitly declared1..9-word entries are supported
 %endif
 extern %1 %+ _impl
 global %1 %+ _far
 %1 %+ _far:
 push bp
 mov bp,sp
 %assign %%argument %2-1
 %rep %2
  push word [bp+6+2*%%argument]
  %assign %%argument %%argument-1
 %endrep
 call %1 %+ _impl
 lea sp,[bp]
 pop bp
 retf
%endmacro
