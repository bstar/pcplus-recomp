; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_close
global files_at_868d
global files_at_868f
global files_at_8692
global files_at_8696
global files_at_8698
global files_at_869b
global files_at_869c
global files_at_869e
global files_at_86a0
global files_at_86a2
global files_at_86a4
global files_at_86a9
extern files_handle_limit
extern files_handle_flags
extern files_error_zero
%else
ORG 0x868c
%define files_handle_limit 0x7b29
%define files_handle_flags 0x7b2b
%define files_error_zero 0x9420
%endif
%include "encodings.inc"
files_close: push bp
files_at_868d: mov_load bp,sp
files_at_868f: mov bx,[bp+0x4]
files_at_8692: cmp bx,[files_handle_limit]
files_at_8696: jc short files_at_869e
files_at_8698: mov ax,0x900
files_at_869b: stc
files_at_869c: jmp short files_at_86a9
files_at_869e: mov ah,0x3e
files_at_86a0: int byte 0x21
files_at_86a2: jc short files_at_86a9
files_at_86a4: mov byte [bx+files_handle_flags],0x0
files_at_86a9: jmp near files_error_zero
