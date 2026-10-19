; Exact native overlay19 EA14..EA1C FGETS_CRLF boolean SET/FETCH wrapper.
BITS 16
CPU 8086
%ifdef ASPECT_SCRIPT_FILE_SETTING_FLAT
ORG 0xea14
%define runtime_script_file_keep_crlf 0xe388
%define aspect_set_boolean 0xe6bb
%else
SEGMENT _TEXT public class=CODE use16
global aspect_script_file_setting
extern _runtime_script_file_keep_crlf,aspect_set_boolean
%define runtime_script_file_keep_crlf _runtime_script_file_keep_crlf
%endif
aspect_script_file_setting:
 mov ax,runtime_script_file_keep_crlf
 push ax
 call aspect_set_boolean
 ret
