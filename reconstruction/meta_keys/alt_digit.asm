; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_alt_digit
extern meta_keys_invoke
extern meta_normalized_scan
extern meta_actions
extern meta_actions_text0
%define short
%else
ORG 0x1594
%define meta_keys_invoke 0x47b6
%define meta_normalized_scan 0xcffa
%define meta_actions 0x3756
%define meta_actions_text0 0x3758
%endif
%include "encodings.inc"
meta_keys_alt_digit:
L_1594: mov ax,0x3
L_1597: push ax
L_1598: mov ax,[meta_normalized_scan]
L_159b: sub ax,strict word 0x78
L_159e: mov cx,0x36
L_15a1: mul cx
L_15a3: mov_load bx,ax
L_15a5: push word [bx+meta_actions]
L_15a9: add bx,meta_actions_text0
L_15ad: push bx
L_15ae: call meta_keys_invoke
L_15b1: add sp,0x6
L_15b4: ret
L_15b5: nop
