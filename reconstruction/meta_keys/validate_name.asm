; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_validate_name
extern meta_keys_message
extern meta_missing_name_message
%define short
%else
ORG 0x4748
%define meta_keys_message 0x427f
%define meta_missing_name_message 0x4416
%endif
%include "encodings.inc"
meta_keys_validate_name:
L_4748: push bp
L_4749: mov_load bp,sp
L_474b: mov bx,[bp+0x4]
L_474e: cmp byte [bx],0x0
L_4751: jz short L_475c
L_4753: cmp byte [bx],0x5b
L_4756: jz short L_475c
L_4758: sub_load ax,ax
L_475a: jmp short L_4766
L_475c: lea bx,[meta_missing_name_message]
L_4760: call meta_keys_message
L_4763: mov ax,0x1
L_4766: mov_load sp,bp
L_4768: pop bp
L_4769: ret
