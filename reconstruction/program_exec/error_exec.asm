; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_error_failure,program_exec_result
extern program_map_error
%define short
%else
ORG 0x9435
%define program_map_error 0x9448
%endif
%include "encodings.inc"
program_exec_result:
L_9435: jnc short L_943e
program_error_failure:
L_9437: call program_map_error
L_943a: mov ax,0xffff
L_943d: cwd
L_943e: mov_load sp,bp
L_9440: pop bp
L_9441: ret
