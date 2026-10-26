; Resident C public names and declared callbacks for CONFIG_CODE.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define CONFIG_ENTRY NEAR_CDECL_ENTRY
%define CONFIG_REGISTER NEAR_NAMED_SERVICE
%define CONFIG_CDECL NEAR_CDECL_SERVICE
; Explicit zero-argument cdecl callbacks use the plain register-free frame.
%define CONFIG_ZERO NEAR_NAMED_SERVICE
%ifdef TERMINAL_DIRECTORY_STORAGE
; Dedicated, exact directory callbacks exceed the old1..4-word service family.
%macro CONFIG_DIRECTORY 3
 %if %3 != 3 && %3 != 6 && %3 != 7
  %error Unknown directory callback ABI
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
%endif
%include "config_abi.inc"
