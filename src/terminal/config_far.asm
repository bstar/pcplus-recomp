; Compiler-generated small-model near functions execute in their own CS.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global terminal_config_code_start
terminal_config_code_start:
%include "far_bridge.inc"
%define CONFIG_ENTRY FAR_CDECL_ENTRY
; Compiler register symbols already include their final trailing underscore.
%macro CONFIG_REGISTER 2
 global %1
 extern %1 %+ _resident
 %1:
 call far %1 %+ _resident
 ret
%endmacro
%define CONFIG_CDECL FAR_CDECL_SERVICE
%macro CONFIG_ZERO 2
 FAR_SERVICE %1
%endmacro
%include "config_abi.inc"
