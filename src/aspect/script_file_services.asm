; Recovered file-status, slot lookup and bounded slot-number helpers.
; The fallback/error boundary is intentionally unresolved in this component.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SCRIPT_FILE_SERVICE_FLAT
%if ASPECT_SCRIPT_FILE_SERVICE_UNIT=1
ORG 0xd943
%elif ASPECT_SCRIPT_FILE_SERVICE_UNIT=2
ORG 0xd956
%elif ASPECT_SCRIPT_FILE_SERVICE_UNIT=3
ORG 0xd97a
%endif
%define aspect_string_bounded_integer 0xdd68
%if ASPECT_SCRIPT_FILE_SERVICE_UNIT!=3
%define aspect_script_file_number 0xd97a
%endif
%define aspect_script_file_error 0x4efb
%define aspect_script_file_slots 0xe39e
%define aspect_script_file_last 0xe3aa
%define aspect_script_file_check 0xe37c
%define aspect_script_file_fallback 0x7b7a
%define aspect_string_compare_result 0xd124
%else
%define ASPECT_SCRIPT_FILE_SERVICE_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_script_file_status,aspect_script_file_lookup,aspect_script_file_number
extern aspect_string_bounded_integer,aspect_script_file_error,aspect_script_file_slots
extern aspect_script_file_last,aspect_script_file_check,aspect_script_file_fallback
extern aspect_string_compare_result
%endif
%if ASPECT_SCRIPT_FILE_SERVICE_UNIT=0 || ASPECT_SCRIPT_FILE_SERVICE_UNIT=1
aspect_script_file_status:
 push bp
 mov_load bp,sp
 mov bx,[bp+4]
 mov al,[bx+6]
 and ax,strict word 0x20
 mov [aspect_string_compare_result],ax
 pop bp
 ret 2
%endif
%if ASPECT_SCRIPT_FILE_SERVICE_UNIT=0 || ASPECT_SCRIPT_FILE_SERVICE_UNIT=2
aspect_script_file_lookup:
 push si
 call aspect_script_file_number
 mov_load bx,ax
 shl bx,1
 mov si,[bx+aspect_script_file_slots]
 or_load si,si
 jnz .done
 cmp [aspect_script_file_check],si
 je .done
 mov ax,4
 push ax
 call aspect_script_file_error
 mov si,aspect_script_file_fallback
.done:
 mov_load ax,si
 pop si
 ret
%endif
%if ASPECT_SCRIPT_FILE_SERVICE_UNIT=0 || ASPECT_SCRIPT_FILE_SERVICE_UNIT=3
aspect_script_file_number:
 sub_load ax,ax
 push ax
 mov ax,5
 push ax
 call aspect_string_bounded_integer
 mov [aspect_script_file_last],ax
 ret
%endif
