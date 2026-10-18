; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_stack_available
global files_at_a8d5
global files_at_a8d8
global files_at_a8da
global files_at_a8dc
global files_at_a8de
global files_at_a8e0
global files_at_a8e2
global files_at_a8e4
extern files_stack_floor
%else
ORG 0xa8d4
%define files_stack_floor 0x7dd6
%endif
%include "encodings.inc"
files_stack_available: pop cx
files_at_a8d5: mov ax,[files_stack_floor]
files_at_a8d8: cmp_load ax,sp
files_at_a8da: jnc short files_at_a8e2
files_at_a8dc: sub_load ax,sp
files_at_a8de: neg ax
files_at_a8e0: jmp cx
files_at_a8e2: xor_load ax,ax
files_at_a8e4: jmp short files_at_a8e0
