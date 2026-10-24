; Recovered PCPlus 2.01 terminal support instructions; see docs/ALTERNATE_OUTPUT.md.
BITS 16
CPU 8086
%ifdef ALTERNATE_OUTPUT_OMF
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
global alternate_output_native
extern alternate_output_attribute
extern erase_previous_attribute
extern text_write_cell
extern render_translation_enabled
extern screen_attributes_base
extern screen_video_offset
%define short
%else
ORG 0xf412
%define alternate_output_attribute 0xf45c
%define erase_previous_attribute 0x2d4c
%define text_write_cell 0x6c5e
%define render_translation_enabled 0x372e
%define screen_attributes_base 0x39c4
%define screen_video_offset 0x3344
%endif
%include "encodings.inc"
alternate_output_native:
L_f412: push bp
L_f413: mov_load bp,sp
L_f415: sub sp,0x2
L_f418: push si
L_f419: cmp word [render_translation_enabled],0x0
L_f41e: jz short L_f434
L_f420: mov si,[bp+0x4]
L_f423: push si
L_f424: call erase_previous_attribute
L_f427: mov [bp-0x1],al
L_f42a: mov bx,[screen_attributes_base]
L_f42e: mov byte [bx+si],0x3
L_f431: jmp short L_f444
L_f433: nop
L_f434: call alternate_output_attribute
L_f437: mov [bp-0x1],al
L_f43a: mov bx,[bp+0x4]
L_f43d: mov si,[screen_attributes_base]
L_f441: mov byte [bx+si],0x1
L_f444: mov al,[bp+0x6]
L_f447: push ax
L_f448: mov al,[bp-0x1]
L_f44b: sub_load ah,ah
L_f44d: push ax
L_f44e: push word [screen_video_offset]
L_f452: call text_write_cell
L_f455: pop si
L_f456: mov_load sp,bp
L_f458: pop bp
L_f459: ret word 0x4
