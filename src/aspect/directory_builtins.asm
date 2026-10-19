; Exact PCPlus2.01 selected-directory ASPECT getters, original SHA256
;6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Overlay16 D9B5..D9B9 (entry), DAA2..DAC2 (eight string pointers).
; Near RET; AX result, flags and all other registers preserved. Strings alias
; the owned selected114-byte record, not literals or freshly allocated copies.
; Original compiler names KBDFILE/METAKEY map to offsets95/86 respectively.
BITS 16
CPU 8086
%ifdef ASPECT_DIRECTORY_FLAT
%define aspect_directory_record 0xe650
%define aspect_directory_entry 0xe482
%if ASPECT_DIRECTORY_UNIT=1
ORG 0xd9b5
%elif ASPECT_DIRECTORY_UNIT=2
ORG 0xdaa2
%else
%error Select ASPECT_DIRECTORY_UNIT1..2
%endif
%else
SEGMENT _TEXT public class=CODE use16
extern aspect_directory_record,aspect_directory_entry
global aspect_directory_builtin_entry,aspect_directory_builtin_ldate
global aspect_directory_builtin_kbdfile,aspect_directory_builtin_metakey
global aspect_directory_builtin_name,aspect_directory_builtin_note
global aspect_directory_builtin_phone,aspect_directory_builtin_pword
global aspect_directory_builtin_script
%endif
%ifnmacro IFUNIT 1
%macro IFUNIT 1
%ifdef ASPECT_DIRECTORY_FLAT
%if ASPECT_DIRECTORY_UNIT=%1
%define DIRECTORY_INCLUDE
%else
%undef DIRECTORY_INCLUDE
%endif
%else
%define DIRECTORY_INCLUDE
%endif
%endmacro
%endif
IFUNIT 1
%ifdef DIRECTORY_INCLUDE
aspect_directory_builtin_entry:
 mov ax,[aspect_directory_entry]
 ret
%endif
IFUNIT 2
%ifdef DIRECTORY_INCLUDE
aspect_directory_builtin_ldate:
 mov ax,aspect_directory_record+61
 ret
aspect_directory_builtin_kbdfile:
 mov ax,aspect_directory_record+95
 ret
aspect_directory_builtin_metakey:
 mov ax,aspect_directory_record+86
 ret
aspect_directory_builtin_name:
 mov ax,aspect_directory_record
 ret
aspect_directory_builtin_note:
 mov ax,aspect_directory_record+105
 ret
aspect_directory_builtin_phone:
 mov ax,aspect_directory_record+25
 ret
aspect_directory_builtin_pword:
 mov ax,aspect_directory_record+75
 ret
aspect_directory_builtin_script:
 mov ax,aspect_directory_record+52
 ret
%endif
