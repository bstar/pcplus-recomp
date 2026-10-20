; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_restore
extern display_snow_disable
extern display_snow_enable
extern display_free
extern display_segment
extern display_cells
%define short
%else
ORG 30040
%define display_snow_disable 30654
%define display_snow_enable 30638
%define display_free 34300
%define display_segment 31352
%define display_cells 31372
%endif
%include "encodings.inc"
display_restore:
L_7558: push bp
L_7559: mov_load bp,sp
L_755b: push di
L_755c: push si
L_755d: mov si,[bp+0x4]
L_7560: mov es,word [display_segment]
L_7564: xor_load di,di
L_7566: call display_snow_disable
L_7569: mov cx,[display_cells]
L_756d: push ds
L_756e: mov ds,word [bp+0x6]
L_7571: rep movsw
L_7573: pop ds
L_7574: call display_snow_enable
L_7577: push word [bp+0x6]
L_757a: push word [bp+0x4]
L_757d: call display_free
L_7580: add sp,0x4
L_7583: pop si
L_7584: pop di
L_7585: pop bp
L_7586: ret word 0x4
