; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_BOUNDARY.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_BOUNDARY_OMF
%ifdef KEYBOARD_ECHO_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_offset_to_position
extern attribute_position_to_video
extern reverse_tab_signed_divide
extern screen_attribute_row_bytes
%define short
%else
ORG 0x2bde
%define attribute_position_to_video 0x2b86
%define reverse_tab_signed_divide 0x830c
%define screen_attribute_row_bytes 0x325a
%endif
%include "encodings.inc"
attribute_offset_to_position:
L_2bde: push bp
L_2bdf: mov_load bp,sp
L_2be1: sub sp,0x4
L_2be4: push si
L_2be5: mov si,[bp+0x4]
L_2be8: push word [screen_attribute_row_bytes]
L_2bec: push word [bp+0x6]
L_2bef: call reverse_tab_signed_divide
L_2bf2: add sp,0x4
L_2bf5: mov [bp-0x2],dx
L_2bf8: mov [si+0x2],ax
L_2bfb: mov ax,[bp-0x2]
L_2bfe: mov [si+0x4],ax
L_2c01: push si
L_2c02: call attribute_position_to_video
L_2c05: pop si
L_2c06: mov_load sp,bp
L_2c08: pop bp
L_2c09: ret word 0x4
