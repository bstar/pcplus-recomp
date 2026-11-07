; Diagnostic resident callbacks. All non-CRT host C uses explicit -ecc.
; These are a bank ABI test, not the production CONFIG_CODE integration.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
; Generic renamed Watcom calls preserve ES. The native CRT routines have
; special compiler-known clobbers, so forwarding must restore ES explicitly.
%macro CRT_SERVICE 2
extern %2
global %1 %+ _resident
%1 %+ _resident:
 push es
 call %2
 pop es
 retf
%endmacro
; Four register words plus one caller stack count; target RET 2 cleans
; only the copy. The module's near thunk removes the original count.
%macro STACK_COUNT 2
extern %2
global %1 %+ _resident
%1 %+ _resident:
 push bp
 mov bp,sp
 push es
 push word [bp+8]
 call %2
 pop es
 pop bp
 retf
%endmacro
%define META_ENTRY NEAR_CDECL_ENTRY
%define META_REGISTER CRT_SERVICE
%define META_COUNT STACK_COUNT
%define META_CDECL NEAR_CDECL_SERVICE
%include "meta_bank_abi.inc"
NEAR_CDECL_ENTRY _key_fault_reset,1
CRT_SERVICE meta_bank_strstr_,strstr_
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
FAR_CDECL_ENTRY _key_fault_reset,1
global meta_bank_strstr_
extern meta_bank_strstr__resident
meta_bank_strstr_:
 call far meta_bank_strstr__resident
 ret
; Force every bank<->host transition beyond a 16-bit near-call displacement.
SEGMENT META_BANK_PAD public align=16 class=FARPAD use16
times 65536 db 0
