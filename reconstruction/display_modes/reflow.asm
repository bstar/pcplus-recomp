; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_reflow
extern display_rows
extern display_select_rows
extern local_status_toggle_46ba
extern status_hidden
extern terminal_reset_original
%else
ORG 0x476a
%define display_rows 0x7a74
%define status_hidden 0x1d46
%define display_select_rows 0x6ef6
%define local_status_toggle_46ba 0x46ba
%define terminal_reset_original 0x20a4
%endif
display_reflow:
L_476a: push bp
L_476b: mov_load bp,sp
L_476d: mov ax,[bp+0x4]
L_4770: cmp [display_rows],ax
L_4774: jz short L_477a
L_4776: push ax
L_4777: call display_select_rows
L_477a: cmp word [status_hidden],0x1
L_477f: sbb_load ax,ax
L_4781: neg ax
L_4783: mov [status_hidden],ax
L_4786: call local_status_toggle_46ba
L_4789: mov ax,0x1
L_478c: push ax
L_478d: call terminal_reset_original
L_4790: pop bx
L_4791: mov_load sp,bp
L_4793: pop bp
L_4794: ret
