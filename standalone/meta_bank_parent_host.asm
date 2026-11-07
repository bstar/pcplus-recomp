; Diagnostic versions of the already-present production callbacks. The new
; production files must not rely on these definitions being linked anew into
; the parent's full _TEXT. DS=SS; filesystem helpers use real register ABI.
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
NEAR_CDECL_ENTRY _key_fault_reset,1
; Test fault injection uses this extra service; not imported by product units.
NEAR_NAMED_SERVICE meta_bank_strstr_,strstr_
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
; Existing parent resource code uses this ordinary CONFIG near thunk.
global config_memcpy_service_
extern config_memcpy_service__resident
config_memcpy_service_:
 call far config_memcpy_service__resident
 ret
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
FAR_CDECL_ENTRY _key_fault_reset,1
global meta_bank_strstr_
extern meta_bank_strstr__resident
meta_bank_strstr_:
 push es
 call far meta_bank_strstr__resident
 pop es
 ret
SEGMENT META_BANK_PAD public align=16 class=FARPAD use16
times 65536 db 0
