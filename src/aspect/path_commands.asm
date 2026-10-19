; Exact PCPlus2.01 ASPECT path commands; unit coordinates/hashes in fixture.
; Near DS=SS, no arguments. String reader returns AX. CHDIR consumes its
; pointer with RET2 and leaves comparison status unchanged. Other helpers
; are cdecl: MKDIR/DELETE store0/FFFF; RMDIR stores the raw DOS return word.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_PATH_FLAT
%if ASPECT_PATH_UNIT=1
ORG 0xe681
%elif ASPECT_PATH_UNIT=2
ORG 0xe8a0
%elif ASPECT_PATH_UNIT=3
ORG 0xe8e3
%elif ASPECT_PATH_UNIT=4
ORG 0xe69a
%endif
%define aspect_string_read 0xdf04
%define aspect_path_change_directory 0x75ae
%define aspect_path_make_directory 0x9c40
%define aspect_path_remove_directory 0xf2c6
%define aspect_path_unlink 0x9086
%define aspect_string_compare_result 0xd124
%else
%define ASPECT_PATH_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_path_chdir,aspect_path_mkdir,aspect_path_rmdir,aspect_path_delete
extern aspect_string_read,aspect_string_compare_result
extern aspect_path_change_directory,aspect_path_make_directory,aspect_path_remove_directory,aspect_path_unlink
%endif
%if ASPECT_PATH_UNIT=0 || ASPECT_PATH_UNIT=1
aspect_path_chdir:
 call aspect_string_read
 push ax
 call aspect_path_change_directory
 ret
%endif
%if ASPECT_PATH_UNIT=0 || ASPECT_PATH_UNIT=2
aspect_path_mkdir:
 call aspect_string_read
 push ax
 call aspect_path_make_directory
 pop bx
 mov [aspect_string_compare_result],ax
 ret
%endif
%if ASPECT_PATH_UNIT=0 || ASPECT_PATH_UNIT=3
aspect_path_rmdir:
 call aspect_string_read
 push ax
 call aspect_path_remove_directory
 pop bx
 mov [aspect_string_compare_result],ax
 ret
%endif
%if ASPECT_PATH_UNIT=0 || ASPECT_PATH_UNIT=4
aspect_path_delete:
 call aspect_string_read
 push ax
 call aspect_path_unlink
 pop bx
 mov [aspect_string_compare_result],ax
 ret
%endif
