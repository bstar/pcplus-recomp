; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_spawnl
extern program_spawnlp
%define short
%else
ORG 0x8d34
%define program_spawnlp 0xa64e
%endif
%include "encodings.inc"
program_spawnl:
L_8d34: push bp
L_8d35: mov_load bp,sp
L_8d37: lea ax,[bp+0x8]
L_8d3a: push ax
L_8d3b: push word [bp+0x6]
L_8d3e: push word [bp+0x4]
L_8d41: call program_spawnlp
L_8d44: mov_load sp,bp
L_8d46: pop bp
L_8d47: ret
