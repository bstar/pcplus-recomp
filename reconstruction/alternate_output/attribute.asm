; Recovered PCPlus 2.01 terminal support instructions; see docs/ALTERNATE_OUTPUT.md.
BITS 16
CPU 8086
%ifdef ALTERNATE_OUTPUT_OMF
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
global alternate_output_attribute
extern alternate_output_read
extern screen_video_offset
extern attributes_protected_value
%define short
%else
ORG 0xf45c
%define alternate_output_read 0x6fa0
%define screen_video_offset 0x3344
%define attributes_protected_value 0x1d36
%endif
%include "encodings.inc"
alternate_output_attribute:
L_f45c: push bp
L_f45d: mov_load bp,sp
L_f45f: sub sp,0x2
L_f462: mov ax,[screen_video_offset]
L_f465: inc ax
L_f466: push ax
L_f467: call alternate_output_read
L_f46a: and al,0xf8
L_f46c: mov [bp-0x1],al
L_f46f: mov al,[attributes_protected_value]
L_f472: and al,0x7
L_f474: or al,[bp-0x1]
L_f477: mov_load sp,bp
L_f479: pop bp
L_f47a: ret
