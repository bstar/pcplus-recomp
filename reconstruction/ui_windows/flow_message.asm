; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global pcplus_flow_message
extern pcplus_screen_save
extern pcplus_screen_restore
extern ui_tick_delay
extern ui_write_string
extern text_fill_cells
extern ui_flow_region_cells
extern ui_flow_video_base
extern ui_flow_coordinate_base
extern ui_flow_suppressed
extern ui_flow_attribute
%define short
%else
ORG 0x31bb
%define pcplus_screen_save 0x765c
%define pcplus_screen_restore 0x7682
%define ui_tick_delay 0x6b98
%define ui_write_string 0x6bf0
%define text_fill_cells 0x6c20
%define ui_flow_region_cells 0x3250
%define ui_flow_video_base 0x7a82
%define ui_flow_coordinate_base 0x7a84
%define ui_flow_suppressed 0x1d46
%define ui_flow_attribute 0x1f6e
%endif
%include "encodings.inc"
pcplus_flow_message:
L_31bb: push bp
L_31bc: mov_load bp,sp
L_31be: sub sp,0x1e
L_31c1: push di
L_31c2: push si
L_31c3: mov di,[ui_flow_region_cells]
L_31c7: sub di,0x50
L_31ca: mov_load ax,di
L_31cc: sar di,1
L_31ce: or di,[ui_flow_coordinate_base]
L_31d2: mov_load si,ax
L_31d4: add si,[ui_flow_video_base]
L_31d8: cmp word [ui_flow_suppressed],0x0
L_31dd: jnz short L_3220
L_31df: lea ax,[bp-0x1e]
L_31e2: push ax
L_31e3: push si
L_31e4: mov ax,0xf
L_31e7: push ax
L_31e8: call pcplus_screen_save
L_31eb: mov ax,[ui_flow_attribute]
L_31ee: or ah,0x20
L_31f1: push ax
L_31f2: push si
L_31f3: mov ax,0xf
L_31f6: push ax
L_31f7: call text_fill_cells
L_31fa: lea ax,[di+0x1]
L_31fd: push ax
L_31fe: push word [ui_flow_attribute]
L_3202: push word [bp+0x4]
L_3205: call ui_write_string
L_3208: cmp word [bp+0x6],0x0
L_320c: jz short L_3220
L_320e: push word [bp+0x6]
L_3211: call ui_tick_delay
L_3214: lea ax,[bp-0x1e]
L_3217: push ax
L_3218: push si
L_3219: mov ax,0xf
L_321c: push ax
L_321d: call pcplus_screen_restore
L_3220: pop si
L_3221: pop di
L_3222: mov_load sp,bp
L_3224: pop bp
L_3225: ret
