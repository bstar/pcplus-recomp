; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_stack_probe
extern program_service_8224
extern program_state_7dd6
%define short
%else
ORG 0xa8bc
%define program_service_8224 0x8224
%define program_state_7dd6 0x7dd6
%endif
%include "encodings.inc"
program_stack_probe:
L_a8bc: pop cx
L_a8bd: mov_load bx,sp
L_a8bf: sub_load bx,ax
L_a8c1: jc short L_a8cd
L_a8c3: cmp bx,[program_state_7dd6]
L_a8c7: jc short L_a8cd
L_a8c9: mov_load sp,bx
L_a8cb: jmp cx
L_a8cd: push cx
L_a8ce: xor_load ax,ax
L_a8d0: jmp near program_service_8224
