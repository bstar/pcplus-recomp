; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_REPAIR.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_REPAIR_OMF
%ifdef ATTRIBUTE_REPAIR_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_repair_write
extern text_write_char
extern screen_viewport_enabled
extern erase_shadow_offset
%define short
%else
ORG 0x2c3a
%define text_write_char 0x6c84
%define screen_viewport_enabled 0xcdfa
%define erase_shadow_offset 0x5dea
%endif
%include "encodings.inc"
attribute_repair_write:
L_2c3a: push bp
L_2c3b: mov_load bp,sp
L_2c3d: push di
L_2c3e: push si
L_2c3f: mov si,[bp+0x4]
L_2c42: cmp word [screen_viewport_enabled],0x0
L_2c47: jz short L_2c5e
L_2c49: cmp word [si],0x0
L_2c4c: jnz short L_2c5e
L_2c4e: mov al,[bp+0x6]
L_2c51: mov bx,[si+0x6]
L_2c54: les di,word [erase_shadow_offset]
L_2c58: mov [es:bx+di],al
L_2c5b: jmp short L_2c6a
L_2c5d: nop
L_2c5e: mov al,[bp+0x6]
L_2c61: sub_load ah,ah
L_2c63: push ax
L_2c64: push word [si+0x6]
L_2c67: call text_write_char
L_2c6a: pop si
L_2c6b: pop di
L_2c6c: mov_load sp,bp
L_2c6e: pop bp
L_2c6f: ret word 0x4
