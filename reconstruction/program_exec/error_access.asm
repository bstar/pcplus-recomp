; Recovered PCPlus 2.01 PROGRAM execution instructions; see docs/PROGRAM_EXEC.md.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
global program_access_result
extern program_error_failure
%define short
%else
ORG 0x9420
%define program_error_failure 0x9437
%endif
%include "encodings.inc"
program_access_result:
L_9420: jc short program_error_failure
L_9422: xor_load ax,ax
L_9424: mov_load sp,bp
L_9426: pop bp
L_9427: ret
