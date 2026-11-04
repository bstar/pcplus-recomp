; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_commit
extern display_policy
extern display_rows
extern display_select_rows
extern display_selector
%else
ORG 0x2f16
%define display_rows 0x7a74
%define display_selector 0x3252
%define display_policy 0x2f58
%define display_select_rows 0x6ef6
%endif
display_commit:
L_2f16: push bp
L_2f17: mov_load bp,sp
L_2f19: push di
L_2f1a: push si
L_2f1b: mov si,[bp+0x4]
L_2f1e: or_load si,si
L_2f20: jz short L_2f2f
L_2f22: cmp si,0x1
L_2f25: jz short L_2f2f
L_2f27: mov di,[bp+0x6]
L_2f2a: cmp si,0x3
L_2f2d: jnz short L_2f33
L_2f2f: mov di,[display_rows]
L_2f33: cmp word [bp+0x8],0x0
L_2f37: jz short L_2f46
L_2f39: cmp [display_rows],di
L_2f3d: jz short L_2f4d
L_2f3f: push di
L_2f40: call display_select_rows
L_2f43: jmp short L_2f4d
L_2f45: nop
L_2f46: push di
L_2f47: call display_policy
L_2f4a: add sp,0x2
L_2f4d: mov [display_selector],si
L_2f51: pop si
L_2f52: pop di
L_2f53: mov_load sp,bp
L_2f55: pop bp
L_2f56: ret
L_2f57: nop
