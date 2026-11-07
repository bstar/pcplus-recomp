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
; Explicit admitted startup lookup. No persistent owner or table adoption.
global _meta_module_resolve
extern _meta_key_resource_lookup
_meta_module_resolve:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call _meta_key_resource_lookup
 lea sp,[bp]
 pop bp
 retf

%ifdef TERMINAL_META_SHARED
FAR_CDECL_ENTRY _meta_front_bank_event,4
FAR_CDECL_ENTRY _meta_front_bank_cursor,0
FAR_CDECL_ENTRY _meta_front_bank_shape,0
FAR_CDECL_ENTRY _meta_front_bank_pending,0
%endif
