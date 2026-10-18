; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_validate_name
extern program_service_427f
extern program_state_4416
%define short
%else
ORG 0x4748
%define program_service_427f 0x427f
%define program_state_4416 0x4416
%endif
%include "encodings.inc"
program_validate_name:
L_4748: push bp
L_4749: mov_load bp,sp
L_474b: mov bx,[bp+0x4]
L_474e: cmp byte [bx],0x0
L_4751: jz short L_475c
L_4753: cmp byte [bx],0x5b
L_4756: jz short L_475c
L_4758: sub_load ax,ax
L_475a: jmp short L_4766
L_475c: lea bx,[program_state_4416]
L_4760: call program_service_427f
L_4763: mov ax,0x1
L_4766: mov_load sp,bp
L_4768: pop bp
L_4769: ret
