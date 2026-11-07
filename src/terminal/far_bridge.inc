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
; Separate entry family supports these known0..10-word APIs; it does not change
; the modem callback family's1..4-word contract or accept variadic/RET N APIs.
%macro NEAR_CDECL_ENTRY 2
 %if %2 < 0 || %2 > 10
  %error Only explicitly declared0..10-word entries are supported
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
 %if %2 < 0 || %2 > 10
  %error Only explicitly declared0..10-word entries are supported
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

; A plain near-cdecl caller has only a return IP above its argument words.
; Widen that return to CS:IP, then tail-enter the unchanged far-cdecl adapter.
; AX is a volatile, non-argument register for this declared stack-only ABI.
; The far adapter still copies arguments before its near implementation call;
; implementation parameter writes therefore cannot modify caller argument slots.
%macro NEAR_CDECL_TAIL_ENTRY 2
 %if %2 < 0 || %2 > 10
  %error Only explicitly declared0..10-word cdecl entries are supported
 %endif
 extern %1 %+ _far
 global %1
 %1:
 pop ax
 push cs
 push ax
 jmp far %1 %+ _far
%endmacro

; Share the far adapter's argument-copy loop in one CS. All inputs are declared
; cdecl stack words. AX/CX are volatile; SI/BP and the caller's slots survive.
%macro FAR_CDECL_SHARED_ENTRY 3
 %if %2 < 0 || %2 > 10
  %error Only explicitly declared0..10-word cdecl entries are supported
 %endif
 extern %1 %+ _impl
 global %1 %+ _far
 %1 %+ _far:
 mov ax,%1 %+ _impl
 mov cl,%2
 jmp near %3
%endmacro
%macro FAR_CDECL_SHARED_BODY 1
 global %1,%1 %+ _end
 %1:
 push bp
 mov bp,sp
 push si
 xor ch,ch
 mov si,cx
 shl si,1
 add si,4
 jcxz %%call
 %%copy:
 push word [bp+si]
 sub si,2
 loop %%copy
 %%call:
 call ax
 lea sp,[bp-2]
 pop si
 pop bp
 retf
 %1 %+ _end:
%endmacro
