; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_get_ds
%define short
%else
ORG 0x76b0
%endif
%include "encodings.inc"
program_get_ds:
L_76b0: mov ax,ds
L_76b2: ret
