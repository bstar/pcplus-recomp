; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_copy_wrapper
global files_at_4736
global files_at_4738
global files_at_473b
global files_at_473e
global files_at_4741
global files_at_4744
global files_at_4746
global files_at_4747
extern files_copy
%else
ORG 0x4735
%define files_copy 0x85b4
%endif
%include "encodings.inc"
files_copy_wrapper: push bp
files_at_4736: mov_load bp,sp
files_at_4738: push word [bp+0x8]
files_at_473b: push word [bp+0x6]
files_at_473e: push word [bp+0x4]
files_at_4741: call files_copy
files_at_4744: mov_load sp,bp
files_at_4746: pop bp
files_at_4747: ret
