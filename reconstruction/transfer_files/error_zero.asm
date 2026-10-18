; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_error_zero
global files_at_9422
global files_at_9424
global files_at_9426
global files_at_9427
extern files_at_9437
%else
ORG 0x9420
%define files_at_9437 0x9437
%endif
%include "encodings.inc"
files_error_zero: jc short files_at_9437
files_at_9422: xor_load ax,ax
files_at_9424: mov_load sp,bp
files_at_9426: pop bp
files_at_9427: ret
