; Resident7f90: one-byte interrupt return, referenced by native7508.
BITS 16
CPU 8086
%ifdef PROGRAM_BREAK_OMF
SEGMENT _TEXT public class=CODE use16
global program_break_ignore
%else
ORG 0x7f90
%endif
program_break_ignore:
 iret
