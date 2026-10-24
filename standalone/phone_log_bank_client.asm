; Diagnostic-only public near entries and existing CONFIG callback substitutes.
; The application already owns CONFIG callbacks; do not link these substitutes.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define PHONE_ENTRY NEAR_CDECL_ENTRY
%macro PHONE_REGISTER 2
%endmacro
%macro PHONE_STACK 2
%endmacro
%include "phone_log_abi.inc"
NEAR_NAMED_SERVICE config_memcpy_service_,memcpy_
NEAR_NAMED_SERVICE config_memset_service_,memset_
NEAR_NAMED_SERVICE config_memcmp_service_,memcmp_
NEAR_NAMED_SERVICE config_strchr_service_,strchr_
NEAR_NAMED_SERVICE config_strcmp_service_,strcmp_
NEAR_NAMED_SERVICE config_strcpy_service_,strcpy_
NEAR_NAMED_SERVICE config_memmove_service_,memmove_
NEAR_NAMED_SERVICE config_canonical_service_,capture_fs_canonical_
NEAR_NAMED_SERVICE config_u4div_service_,__U4D
NEAR_NAMED_SERVICE config_u4mul_service_,__U4M
