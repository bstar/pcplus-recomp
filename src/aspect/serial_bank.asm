BITS 16
CPU 8086
%macro SERIAL_ENTRY 2
 %if %2 < 0 || %2 > 1
  %error Serial public entry count must be0 or1
 %endif
 global %1
 %1:
 push bp
 mov bp,sp
 %if %2
 push word [bp+4]
 %endif
 call far %1 %+ _far
 lea sp,[bp]
 pop bp
 ret
%endmacro
%macro SERIAL_CALLBACK 3
 %assign %%count %3
 %ifdef ASPECT_CUSTOM_IRQ
  %ifidni %1,_serial_bank_backend_open
   %assign %%count 5
  %endif
 %endif
 %if %%count < 0 || %%count > 6
  %error Serial callback count must be0..6
 %endif
 extern %2
 global %1 %+ _resident
 %1 %+ _resident:
 push bp
 mov bp,sp
 %assign %%arg %%count-1
 %rep %%count
 push word [bp+8+2*%%arg]
 %assign %%arg %%arg-1
 %endrep
 call %2
 lea sp,[bp]
 pop bp
 retf
%endmacro
SEGMENT _TEXT public class=CODE use16
%include "serial_bank.inc"
%unmacro SERIAL_ENTRY 2
%unmacro SERIAL_CALLBACK 3
%macro SERIAL_ENTRY 2
 extern %1 %+ _impl
 global %1 %+ _far
 %1 %+ _far:
 push bp
 mov bp,sp
 %if %2
 push word [bp+6]
 %endif
 call %1 %+ _impl
 lea sp,[bp]
 pop bp
 retf
%endmacro
%macro SERIAL_CALLBACK 3
 global %1
 %1:
 call far %1 %+ _resident
 ret
%endmacro
SEGMENT ASIO_CODE public align=16 class=FARCODE use16
%include "serial_bank.inc"
