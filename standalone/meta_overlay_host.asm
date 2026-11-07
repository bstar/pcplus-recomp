; Diagnostic host with the production services and only test near API entries.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define META_ENTRY NEAR_CDECL_ENTRY
%macro META_REGISTER 2
%endmacro
%define META_COUNT META_REGISTER
%macro META_CDECL 3
%endmacro
%include "meta_bank_abi.inc"
%macro crt 1
 NEAR_NAMED_SERVICE config_%1_service_,%1_
%endmacro
crt memcpy
crt memset
crt memcmp
crt strchr
crt strcmp
crt strlen
NEAR_NAMED_SERVICE config_canonical_service_,capture_fs_canonical_
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global config_memcpy_service_
extern config_memcpy_service__resident
config_memcpy_service_:
 call far config_memcpy_service__resident
 ret
SEGMENT META_OVERLAY_ARENA public align=16 class=FARSTATE use16
GROUP META_OVERLAY_ARENA_GROUP META_OVERLAY_ARENA
global _editor,_live,_proposal
_editor: times 63000 db 0
_live: times 540 db 0
_proposal: times 540 db 0
