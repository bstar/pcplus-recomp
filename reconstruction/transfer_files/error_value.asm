; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_error_value
global files_at_9437
global files_at_943a
global files_at_943d
global files_at_943e
global files_at_9440
global files_at_9441
extern program_map_error
%else
ORG 0x9435
%define program_map_error 0x9448
%endif
%include "encodings.inc"
files_error_value: jnc short files_at_943e
files_at_9437: call program_map_error
files_at_943a: mov ax,0xffff
files_at_943d: cwd
files_at_943e: mov_load sp,bp
files_at_9440: pop bp
files_at_9441: ret
