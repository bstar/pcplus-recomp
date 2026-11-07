; Explicit caller-cleaned entry frames; no near inter-segment calls.
BITS 16
CPU 8086
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
%include "far_bridge.inc"
%define META_ENTRY FAR_CDECL_ENTRY
%macro META_REGISTER 2
%endmacro
%define META_COUNT META_REGISTER
%macro META_CDECL 3
%endmacro
%include "meta_bank_abi.inc"
