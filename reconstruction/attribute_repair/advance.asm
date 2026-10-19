; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_REPAIR.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_REPAIR_OMF
%ifdef ATTRIBUTE_REPAIR_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_repair_advance
extern attribute_position_to_video
extern screen_viewport_enabled
extern screen_viewport_left
extern screen_columns
extern screen_attribute_row_bytes
%define short
%else
ORG 0x2cf2
%define attribute_position_to_video 0x2b86
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_left 0xce2e
%define screen_columns 0x7a72
%define screen_attribute_row_bytes 0x325a
%endif
%include "encodings.inc"
attribute_repair_advance:
L_2cf2: push bp
L_2cf3: mov_load bp,sp
L_2cf5: push si
L_2cf6: mov si,[bp+0x4]
L_2cf9: inc word [si+0x4]
L_2cfc: cmp word [screen_viewport_enabled],0x0
L_2d01: jz short L_2d1a
L_2d03: mov ax,[screen_viewport_left]
L_2d06: cmp [si+0x4],ax
L_2d09: jz short L_2d13
L_2d0b: mov ax,[screen_columns]
L_2d0e: cmp [si+0x4],ax
L_2d11: jnz short L_2d1a
L_2d13: push si
L_2d14: call attribute_position_to_video
L_2d17: jmp short L_2d30
L_2d19: nop
L_2d1a: mov ax,[screen_attribute_row_bytes]
L_2d1d: cmp [si+0x4],ax
L_2d20: jnz short L_2d2c
L_2d22: mov word [si+0x4],0x0
L_2d27: inc word [si+0x2]
L_2d2a: jmp short L_2d13
L_2d2c: add word [si+0x6],0x2
L_2d30: pop si
L_2d31: mov_load sp,bp
L_2d33: pop bp
L_2d34: ret word 0x2
