; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_dispatch
extern display_baseline
extern display_commit
extern display_font_capable
extern display_set_mode
extern preferred_video_mode
extern screen_set_cursor
%else
ORG 0x2eaa
%define preferred_video_mode 0x2070
%define display_font_capable 0x7a6e
%define display_commit 0x2f16
%define display_baseline 0x6f76
%define screen_set_cursor 0x1bbe
%define display_set_mode 0x6f3e
%endif
display_dispatch:
L_2eaa: push bp
L_2eab: mov_load bp,sp
L_2ead: push si
L_2eae: mov si,[bp+0x4]
L_2eb1: sub_load ax,ax
L_2eb3: cwd
L_2eb4: call screen_set_cursor
L_2eb7: mov_load ax,si
L_2eb9: or_load ax,ax
L_2ebb: jz short L_2f04
L_2ebd: sub ax,strict word 1
L_2ec0: jc short L_2f11
L_2ec2: sub ax,strict word 1
L_2ec5: jna short L_2ed6
L_2ec7: sub ax,strict word 1
L_2eca: jc short L_2f11
L_2ecc: sub ax,strict word 1
L_2ecf: jna short L_2edc
L_2ed1: pop si
L_2ed2: mov_load sp,bp
L_2ed4: pop bp
L_2ed5: ret
L_2ed6: call display_baseline
L_2ed9: jmp short L_2f04
L_2edb: nop
L_2edc: cmp word [preferred_video_mode],0x0
L_2ee1: jng short L_2ef4
L_2ee3: cmp word [display_font_capable],0x0
L_2ee8: jz short L_2ef4
L_2eea: push word [preferred_video_mode]
L_2eee: call display_set_mode
L_2ef1: jmp short L_2f04
L_2ef3: nop
L_2ef4: call display_baseline
L_2ef7: push word [bp+0x8]
L_2efa: push word [bp+0x6]
L_2efd: mov ax,0x1
L_2f00: push ax
L_2f01: jmp short L_2f0b
L_2f03: nop
L_2f04: push word [bp+0x8]
L_2f07: push word [bp+0x6]
L_2f0a: push si
L_2f0b: call display_commit
L_2f0e: add sp,0x6
L_2f11: pop si
L_2f12: mov_load sp,bp
L_2f14: pop bp
L_2f15: ret
