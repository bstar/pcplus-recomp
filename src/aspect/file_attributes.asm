; PCPlus2.01 GETFATTR/SETFATTR and DOS21 AH43 helpers. Flat baseline is
; unchanged; maintained GET uses destination selection + far writeback.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FILE_ATTRIBUTES_FLAT
%if ASPECT_FILE_ATTRIBUTES_UNIT=1
ORG 0xed45
%elif ASPECT_FILE_ATTRIBUTES_UNIT=2
ORG 0xed69
%elif ASPECT_FILE_ATTRIBUTES_UNIT=3
ORG 0xf311
%elif ASPECT_FILE_ATTRIBUTES_UNIT=4
ORG 0xf323
%endif
%define aspect_string_read 0xdf04
%define enum_format_attributes 0xee23
%define enum_parse_attributes 0xeda4
%define aspect_string_compare_result 0xd124
%if ASPECT_FILE_ATTRIBUTES_UNIT!=3
%define file_attributes_get 0xf311
%endif
%if ASPECT_FILE_ATTRIBUTES_UNIT!=4
%define file_attributes_set 0xf323
%endif
%else
%define ASPECT_FILE_ATTRIBUTES_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_file_attributes_get,aspect_file_attributes_set
extern aspect_string_read,aspect_string_read_destination,aspect_string_flush
extern enum_format_attributes,enum_parse_attributes,aspect_string_compare_result
%endif
%if ASPECT_FILE_ATTRIBUTES_UNIT=0 || ASPECT_FILE_ATTRIBUTES_UNIT=1
aspect_file_attributes_get:
 push si
 call aspect_string_read
 push ax
 call file_attributes_get
 pop bx
 mov_load si,ax
 push si
%ifdef ASPECT_FILE_ATTRIBUTES_RUNTIME
 call aspect_string_read_destination
%else
 call aspect_string_read
%endif
 push ax
 call enum_format_attributes
%ifdef ASPECT_FILE_ATTRIBUTES_RUNTIME
 call aspect_string_flush
%endif
 mov_load ax,si
 inc ax
 jnz .success
 mov ax,1
 jmp short .done
.success:
 sub_load ax,ax
.done:
 mov [aspect_string_compare_result],ax
 pop si
 ret
%endif
%if ASPECT_FILE_ATTRIBUTES_UNIT=0 || ASPECT_FILE_ATTRIBUTES_UNIT=2
aspect_file_attributes_set:
 push si
 call aspect_string_read
 mov_load si,ax
 call aspect_string_read
 push ax
 sub_load ax,ax
 push ax
 call enum_parse_attributes
 push ax
 push si
 call file_attributes_set
 pop bx
 pop bx
 mov [aspect_string_compare_result],ax
 pop si
 ret
%endif
%if ASPECT_FILE_ATTRIBUTES_UNIT=0 || ASPECT_FILE_ATTRIBUTES_UNIT=3
file_attributes_get:
 mov_load bx,sp
 mov ax,0x4300
 mov dx,[bx+2]
 int 0x21
 jnc .done
 mov cx,0xffff
.done:
 mov_load ax,cx
 ret
%endif
%if ASPECT_FILE_ATTRIBUTES_UNIT=0 || ASPECT_FILE_ATTRIBUTES_UNIT=4
file_attributes_set:
 mov_load bx,sp
 mov ax,0x4301
 mov cx,[bx+4]
 mov dx,[bx+2]
 int 0x21
 jc .done
 xor_load ax,ax
.done:
 ret
%endif
