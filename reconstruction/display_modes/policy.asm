; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_policy
extern display_reflow
extern display_reset_policy
extern terminal_reset_policy
%else
ORG 0x2f58
%define terminal_reset_policy 0x1d2e
%define display_reset_policy 0x3254
%define display_reflow 0x476a
%endif
display_policy:
L_2f58: push bp
L_2f59: mov_load bp,sp
L_2f5b: push si
L_2f5c: mov si,[terminal_reset_policy]
L_2f60: mov ax,[display_reset_policy]
L_2f63: mov [terminal_reset_policy],ax
L_2f66: push word [bp+0x4]
L_2f69: call display_reflow
L_2f6c: add sp,0x2
L_2f6f: mov [terminal_reset_policy],si
L_2f73: pop si
L_2f74: mov_load sp,bp
L_2f76: pop bp
L_2f77: ret
