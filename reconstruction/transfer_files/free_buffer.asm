; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_free_buffer
global files_at_a001
global files_at_a003
global files_at_a004
global files_at_a007
global files_at_a00a
global files_at_a00c
global files_at_a00e
global files_at_a010
global files_at_a012
global files_at_a015
global files_at_a018
global files_at_a019
global files_at_a01d
global files_at_a01f
global files_at_a022
global files_at_a024
global files_at_a027
global files_at_a028
global files_at_a029
extern files_heap_free
%else
ORG 0xa000
%define files_heap_free 0x92a4
%endif
%include "encodings.inc"
files_free_buffer: push bp
files_at_a001: mov_load bp,sp
files_at_a003: push si
files_at_a004: mov si,[bp+0x4]
files_at_a007: mov al,[si+0x6]
files_at_a00a: test al,0x83
files_at_a00c: jz short files_at_a027
files_at_a00e: test al,0x8
files_at_a010: jz short files_at_a027
files_at_a012: push word [si+0x4]
files_at_a015: call files_heap_free
files_at_a018: pop cx
files_at_a019: and byte [si+0x6],0xf7
files_at_a01d: xor_load ax,ax
files_at_a01f: mov [si+0x4],ax
files_at_a022: mov [si],ax
files_at_a024: mov [si+0x2],ax
files_at_a027: pop si
files_at_a028: pop bp
files_at_a029: ret
