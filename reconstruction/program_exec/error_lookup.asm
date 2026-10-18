; Recovered DOS-to-CRT error mapping, originalDS7b56.
BITS 16
%ifdef PROGRAM_EXEC_OMF
SEGMENT _DATA public align=16 class=DATA use16
global program_error_map
%endif
program_error_map: db 0,22,2,2,24,13,9,12,12,12,7,8,22,22,255,2,13,18,2,255
