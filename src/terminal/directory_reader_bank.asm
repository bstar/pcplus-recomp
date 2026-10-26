; Explicit small-model cdecl FS adapters; the reader preserves DS=SS and passes
; near DOS buffers. No implicit stack forwarding or serial/UI ownership.
BITS 16
CPU 8086
%include "far_bridge.inc"
%ifdef TERMINAL_DIRECTORY_VIEW
SEGMENT _TEXT public class=CODE use16
SEGMENT DIRECTORY_CODE public align=16 class=FARCODE use16
GROUP DIRECTORY_GROUP DIRECTORY_CODE
%macro DIRECTORY_REGISTER 2
 SEGMENT _TEXT
 NEAR_NAMED_SERVICE %1,%2
 SEGMENT DIRECTORY_CODE
 global %1
 %1:
 call far %1 %+ _resident
 ret
%endmacro
; The live application keeps its small filesystem wrappers in the same bank
; as the reader. Only the actual DOS CRT register calls cross into resident CS.
DIRECTORY_REGISTER directory_dos_open_service_,_dos_open_
DIRECTORY_REGISTER directory_dos_close_service_,_dos_close_
; Watcom's DOS read uses AX/BX/CX/DX plus one stack output pointer, and RET2.
; Forward that declared word into the resident frame; remove the original
; only after the far call returns. A plain register thunk corrupts both frames.
SEGMENT _TEXT
extern _dos_read_
global directory_dos_read_service__resident
directory_dos_read_service__resident:
 push bp
 mov bp,sp
 push word [bp+8]
 call _dos_read_
 pop bp
 retf
SEGMENT DIRECTORY_CODE
global directory_dos_read_service_
directory_dos_read_service_:
 call far directory_dos_read_service__resident
 ret 2
%else
SEGMENT _TEXT public class=CODE use16
NEAR_CDECL_SERVICE _directory_reader_bank_open,_directory_reader_fs_open,2
NEAR_CDECL_SERVICE _directory_reader_bank_read,_directory_reader_fs_read,4
NEAR_CDECL_SERVICE _directory_reader_bank_close,_directory_reader_fs_close,1
SEGMENT DIRECTORY_CODE public align=16 class=FARCODE use16
GROUP DIRECTORY_GROUP DIRECTORY_CODE
FAR_CDECL_SERVICE _directory_reader_bank_open,_directory_reader_fs_open,2
FAR_CDECL_SERVICE _directory_reader_bank_read,_directory_reader_fs_read,4
FAR_CDECL_SERVICE _directory_reader_bank_close,_directory_reader_fs_close,1
%endif
%ifdef TERMINAL_DIRECTORY_VIEW
; Give the existing menu bank its own paragraph-aligned CS when the directory
; bank precedes it. It must not inherit a nonzero AUTO-group offset.
SEGMENT REFERENCE_CODE public align=16 class=FARCODE use16
GROUP REFERENCE_GROUP REFERENCE_CODE
%endif
