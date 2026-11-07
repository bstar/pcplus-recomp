; Transient Meta bank imports. Every near call stays in this code segment;
; parent callbacks must supply the declared far resident ABI with DS=SS.
BITS 16
CPU 8086
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
%macro imported 1
global %1
extern %1 %+ _resident
%1:
 call far %1 %+ _resident
 ret
%endmacro
; Watcom far memcpy/memcmp take four register words plus a fifth stack
; count, removed by RET 2. The resident adapter copies that count explicitly.
%macro stack_count 1
global %1
extern %1 %+ _resident
%1:
 call far %1 %+ _resident
 ret 2
%endmacro
%macro META_ENTRY 2
%endmacro
%macro META_REGISTER 2
 imported %1
%endmacro
%macro META_COUNT 2
 stack_count %1
%endmacro
%macro META_CDECL 3
 imported %1
%endmacro
%include "meta_bank_abi.inc"
