; Recovered PCPlus 2.01 character editing instructions; see docs/CHARACTER_EDIT.md.
BITS 16
CPU 8086
%ifdef CHARACTER_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_set_tab
extern screen_cursor_column
extern terminal_tab_stops
%define short
%else
ORG 0xdac6
%define screen_cursor_column 0x399e
%define terminal_tab_stops 0xce10
%endif
%include "encodings.inc"
terminal_set_tab:
L_dac6: push di
L_dac7: sub_load bx,bx
L_dac9: mov al,[screen_cursor_column]
L_dacc: cmp [bx+terminal_tab_stops],al
L_dad0: jz short L_daf0
L_dad2: ja short L_dadc
L_dad4: inc bx
L_dad5: cmp bx,0x1e
L_dad8: jl short L_dac9
L_dada: pop di
L_dadb: ret
L_dadc: mov di,0x1c
L_dadf: cmp_load bx,di
L_dae1: jnl short L_dae9
L_dae3: sub_load bx,di
L_dae5: neg bx
L_dae7: sub_load di,bx
L_dae9: mov al,[screen_cursor_column]
L_daec: mov [di+terminal_tab_stops],al
L_daf0: pop di
L_daf1: ret
