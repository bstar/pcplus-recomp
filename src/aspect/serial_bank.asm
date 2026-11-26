BITS 16
CPU 8086
%macro SERIAL_ENTRY 2
 %if %2 < 0 || %2 > 1
  %error Serial public entry count must be0 or1
 %endif
 global %1
 %1:
 %ifdef ASPECT_SERIAL_OVERLAY_READY
  %ifidni %1,_aspect_serial_directory_entry
   mov ax,[_aspect_serial_directory_entry_data]
   ret
   %exitmacro
  %elifidni %1,_aspect_serial_directory_record
   xor ax,ax
   cmp word [_aspect_serial_directory_entry_data],0
   je %%done
   mov ax,_aspect_serial_directory_record_data
  %%done:
   ret
   %exitmacro
  %elifidni %1,_aspect_serial_translation_policy
   mov ax,[_aspect_serial_input_translation_mode]
   ret
   %exitmacro
  %elifidni %1,_aspect_serial_translate
   push bp
   mov bp,sp
   mov ax,[bp+4]
   xor ah,ah
   cmp word [_aspect_serial_input_translation_mode],1
   jne %%done
   push bx
   mov bx,ax
   mov al,[_aspect_serial_input_translation+bx]
   pop bx
  %%done:
   pop bp
   ret
   %exitmacro
  %endif
 %endif
 %ifdef SERIAL_BANK_ROOT_ONLY
  extern %1 %+ _far
 %endif
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
%ifndef SERIAL_BANK_OVERLAY_ONLY
 SEGMENT _TEXT public class=CODE use16
 %ifdef ASPECT_SERIAL_OVERLAY_READY
  extern _aspect_serial_input_translation,_aspect_serial_input_translation_mode
  extern _aspect_serial_directory_record_data,_aspect_serial_directory_entry_data
 %endif
 %include "serial_bank.inc"
%endif
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
 %ifdef SERIAL_BANK_OVERLAY_ONLY
  extern %1 %+ _resident
 %endif
 global %1
 %1:
 call far %1 %+ _resident
 ret
%endmacro
%ifndef SERIAL_BANK_ROOT_ONLY
 SEGMENT ASIO_CODE public align=16 class=FARCODE use16
 %include "serial_bank.inc"
%endif
