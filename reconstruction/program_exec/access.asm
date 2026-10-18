; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_access
extern program_access_result
%define short
%else
ORG 0x93aa
%define program_access_result 0x9420
%endif
%include "encodings.inc"
program_access:
L_93aa: push bp
L_93ab: mov_load bp,sp
L_93ad: mov dx,[bp+0x4]
L_93b0: mov ax,0x4300
L_93b3: int byte 0x21
L_93b5: jc short L_93c6
L_93b7: test byte [bp+0x6],0x2
L_93bb: jz short L_93c6
L_93bd: test cl,0x1
L_93c0: jz short L_93c6
L_93c2: mov ax,0xd00
L_93c5: stc
L_93c6: jmp near program_access_result
