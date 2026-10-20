%ifdef PROGRAM_BREAK_OMF
%ifdef NATIVE_BREAK_FAR
SEGMENT BRKCODE public class=CODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
extern program_break_original_1b,program_break_original_23,program_break_original_flag
%else
%define program_break_original_1b 0x7ab6
%define program_break_original_23 0x7aba
%define program_break_original_flag 0x7abe
%endif
