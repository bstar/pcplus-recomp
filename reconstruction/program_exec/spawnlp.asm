; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_spawnlp
extern program_spawn_search
extern program_stack_probe
extern program_environ
%define short
%else
ORG 0xa64e
%define program_spawn_search 0xa4a6
%define program_stack_probe 0xa8bc
%define program_environ 0x7b43
%endif
%include "encodings.inc"
program_spawnlp:
L_a64e: push bp
L_a64f: mov_load bp,sp
L_a651: xor_load ax,ax
L_a653: call program_stack_probe
L_a656: push word [program_environ]
L_a65a: push word [bp+0x8]
L_a65d: push word [bp+0x6]
L_a660: push word [bp+0x4]
L_a663: call program_spawn_search
L_a666: mov_load sp,bp
L_a668: pop bp
L_a669: ret
