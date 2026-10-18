; Exact zero-initialized original CS6a18..6a21 execution save cells.
BITS 16
%ifdef PROGRAM_EXEC_OMF
SEGMENT _TEXT public class=CODE use16
%else
ORG 0x6a18
%endif
%ifdef PROGRAM_EXEC_OMF
global program_saved_sp
%endif
program_saved_sp: dw 0
%ifdef PROGRAM_EXEC_OMF
global program_saved_ss
%endif
program_saved_ss: dw 0
%ifdef PROGRAM_EXEC_OMF
global program_saved_pair_low
%endif
program_saved_pair_low: dw 0
%ifdef PROGRAM_EXEC_OMF
global program_saved_pair_high
%endif
program_saved_pair_high: dw 0
%ifdef PROGRAM_EXEC_OMF
global program_saved_ds
%endif
program_saved_ds: dw 0
