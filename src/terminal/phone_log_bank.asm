; Dedicated small-model C bank. No resident public-entry trampolines required
; by assembly callers: call the declared *_far entry directly.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=16 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
global terminal_phone_log_code_start
terminal_phone_log_code_start:
%include "far_bridge.inc"
%define PHONE_ENTRY FAR_CDECL_ENTRY
%macro PHONE_REGISTER 2
 global %1
 extern %1 %+ _resident
 %1:
 call far %1 %+ _resident
 ret
%endmacro
%macro PHONE_STACK 2
 global %1
 extern %1 %+ _resident
 %1:
 call far %1 %+ _resident
 ret 2
%endmacro
%include "phone_log_abi.inc"
; Reuse existing CONFIG resident CRT/canonical callbacks in the application.
%macro PHONE_SHARED 2
 global %1
 extern %2 %+ _resident
 %1:
 call far %2 %+ _resident
 ret
%endmacro
PHONE_SHARED phone_memcpy_service_,config_memcpy_service_
PHONE_SHARED phone_memset_service_,config_memset_service_
PHONE_SHARED phone_memcmp_service_,config_memcmp_service_
PHONE_SHARED phone_strchr_service_,config_strchr_service_
PHONE_SHARED phone_strcmp_service_,config_strcmp_service_
PHONE_SHARED phone_strcpy_service_,config_strcpy_service_
PHONE_SHARED phone_memmove_service_,config_memmove_service_
PHONE_SHARED phone_canonical_service_,config_canonical_service_
PHONE_SHARED phone_u4div_service_,config_u4div_service_
PHONE_SHARED phone_u4mul_service_,config_u4mul_service_
