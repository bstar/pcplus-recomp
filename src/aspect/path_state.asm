; Native numeric DOS error map, expressed as source facts (20 entries).
; The production path owner targets DOS3+; that selects the native >=3 mapping.
; Error fields retain prior values on success, as in the native CRT paths.
BITS 16
CPU 8086
%ifdef ASPECT_PATH_MAP_FLAT
ORG 0x7b56
%else
SEGMENT _DATA public class=DATA use16
global program_errno,program_dos_error,program_dos_major,program_error_map
global _runtime_path_errno,_runtime_path_dos_error
program_errno:
_runtime_path_errno: dw 0
%ifdef ASPECT_EXTERNAL_PROCESS
global _native_crt_error,_native_dos_error,_native_dos_major
_native_crt_error equ program_errno
%endif
program_dos_error:
%ifdef ASPECT_EXTERNAL_PROCESS
_runtime_path_dos_error:
_native_dos_error: dw 0
_native_dos_major:
%else
_runtime_path_dos_error: db 0
%endif
program_dos_major: db 3
program_error_map:
%endif
 db 0,22,2,2,24,13,9,12,12,12,7,8,22,22,255,2,13,18,2,255
