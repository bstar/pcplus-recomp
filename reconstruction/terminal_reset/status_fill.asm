; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
%ifdef STATUS_CONFIG_CODE
SEGMENT CONFIG_CODE public class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global terminal_reset_status_fill
extern text_fill_cells
extern program_state_7a72
extern ui_flow_video_base
extern reset_data_1f6c
%define short
%else
ORG 0x4097
%define text_fill_cells 0x6c20
%define program_state_7a72 0x7a72
%define ui_flow_video_base 0x7a82
%define reset_data_1f6c 0x1f6c
%endif
%include "encodings.inc"
terminal_reset_status_fill:
L_4097: mov ax,[reset_data_1f6c]
L_409a: or ah,0x20
L_409d: push ax
L_409e: push word [ui_flow_video_base]
L_40a2: push word [program_state_7a72]
L_40a6: call text_fill_cells
L_40a9: ret
