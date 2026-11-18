; Exact PCPlus2.01 overlay16 clock string getters:
; DAC2..DAC5 DATE, DAFF..DB07 TIME0, DB07..DB10 TIME1.
; Return aliases to the existing shared date/time formatter buffers.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CLOCK_BUILTINS_FLAT
%if ASPECT_CLOCK_BUILTINS_UNIT=1
ORG 0xdac2
%elif ASPECT_CLOCK_BUILTINS_UNIT=2
ORG 0xdaff
%elif ASPECT_CLOCK_BUILTINS_UNIT=3
ORG 0xdb07
%else
%error Select ASPECT_CLOCK_BUILTINS_UNIT1..3
%endif
%define directory_accounting_date_original 0x36d4
%define aspect_clock_time_format 0x498b
%else
%define ASPECT_CLOCK_BUILTINS_UNIT 0
SEGMENT _TEXT public class=CODE use16
extern directory_accounting_date_original,aspect_clock_time_format
global aspect_builtin_date,aspect_builtin_time0,aspect_builtin_time1
%endif

%if ASPECT_CLOCK_BUILTINS_UNIT=0 || ASPECT_CLOCK_BUILTINS_UNIT=1
aspect_builtin_date:
 jmp directory_accounting_date_original
%endif
%if ASPECT_CLOCK_BUILTINS_UNIT=0 || ASPECT_CLOCK_BUILTINS_UNIT=2
aspect_builtin_time0:
 sub_load ax,ax
 push ax
 call aspect_clock_time_format
 pop bx
 ret
%endif
%if ASPECT_CLOCK_BUILTINS_UNIT=0 || ASPECT_CLOCK_BUILTINS_UNIT=3
aspect_builtin_time1:
 mov ax,1
 push ax
 call aspect_clock_time_format
 pop bx
 ret
%endif
