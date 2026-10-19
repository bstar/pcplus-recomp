; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_REPAIR.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_REPAIR_OMF
%ifdef ATTRIBUTE_REPAIR_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_repair_native
extern attribute_repair_write
extern attribute_repair_advance
extern attribute_position_to_video
extern erase_default_attribute
extern erase_previous_attribute
extern screen_cursor_wrap
extern screen_cursor_row
extern screen_cursor_column
extern erase_cell_count
extern screen_attribute_offset
extern attributes_current
extern screen_attributes_base
extern erase_attribute_values_base
extern attributes_protected_value
extern attributes_normal_value
%define short
%else
ORG 0x2d98
%define attribute_repair_write 0x2c3a
%define attribute_repair_advance 0x2cf2
%define attribute_position_to_video 0x2b86
%define erase_default_attribute 0x2d38
%define erase_previous_attribute 0x2d4c
%define screen_cursor_wrap 0x900c
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define erase_cell_count 0x325c
%define screen_attribute_offset 0x3346
%define attributes_current 0x1f70
%define screen_attributes_base 0x39c4
%define erase_attribute_values_base 0x39c2
%define attributes_protected_value 0x1d36
%define attributes_normal_value 0x1d32
%endif
%include "encodings.inc"
attribute_repair_native:
L_2d98: push bp
L_2d99: mov_load bp,sp
L_2d9b: sub sp,0xe
L_2d9e: push di
L_2d9f: push si
L_2da0: cmp word [screen_cursor_wrap],0x0
L_2da5: jnz short L_2daa
L_2da7: jmp near L_2ea2
L_2daa: mov di,[bp+0x4]
L_2dad: or_load di,di
L_2daf: jz short L_2de8
L_2db1: mov ax,[screen_cursor_row]
L_2db4: mov [bp-0xa],ax
L_2db7: mov ax,[screen_cursor_column]
L_2dba: mov [bp-0x8],ax
L_2dbd: mov ax,[erase_cell_count]
L_2dc0: mov si,[screen_attribute_offset]
L_2dc4: sub_load ax,si
L_2dc6: mov [bp-0x4],ax
L_2dc9: cmp di,0x1
L_2dcc: jnz short L_2dd4
L_2dce: mov al,[attributes_current]
L_2dd1: jmp short L_2dd8
L_2dd3: nop
L_2dd4: push si
L_2dd5: call erase_previous_attribute
L_2dd8: mov [bp-0x1],al
L_2ddb: cmp di,0x3
L_2dde: jnz short L_2dfc
L_2de0: mov word [bp+0x4],0x0
L_2de5: jmp short L_2dfc
L_2de7: nop
L_2de8: sub_load si,si
L_2dea: mov [bp-0x8],si
L_2ded: mov [bp-0xa],si
L_2df0: mov ax,[erase_cell_count]
L_2df3: mov [bp-0x4],ax
L_2df6: call erase_default_attribute
L_2df9: mov [bp-0x1],al
L_2dfc: lea ax,[bp-0xc]
L_2dff: push ax
L_2e00: call attribute_position_to_video
L_2e03: inc word [bp-0x6]
L_2e06: mov bx,[screen_attributes_base]
L_2e0a: mov al,[bx+si]
L_2e0c: and al,0x80
L_2e0e: cmp al,0x1
L_2e10: sbb_load di,di
L_2e12: neg di
L_2e14: mov ax,[bp-0x4]
L_2e17: dec word [bp-0x4]
L_2e1a: or_load ax,ax
L_2e1c: jnz short L_2e21
L_2e1e: jmp near L_2ea2
L_2e21: mov bx,[screen_attributes_base]
L_2e25: mov al,[bx+si]
L_2e27: mov [bp-0xe],al
L_2e2a: test al,0x80
L_2e2c: jz short L_2e62
L_2e2e: cmp word [bp+0x4],0x0
L_2e32: jz short L_2e56
L_2e34: test byte [bp-0xe],0x1
L_2e38: jz short L_2e42
L_2e3a: mov al,[attributes_protected_value]
L_2e3d: jmp short L_2e45
L_2e3f: nop
L_2e40: nop
L_2e41: nop
L_2e42: mov al,[attributes_normal_value]
L_2e45: push ax
L_2e46: lea ax,[bp-0xc]
L_2e49: push ax
L_2e4a: call attribute_repair_write
L_2e4d: or_load di,di
L_2e4f: jnz short L_2ea2
L_2e51: mov di,0x1
L_2e54: jmp short L_2e7c
L_2e56: mov bx,[erase_attribute_values_base]
L_2e5a: mov al,[bx+si]
L_2e5c: mov [bp-0x1],al
L_2e5f: jmp short L_2e7c
L_2e61: nop
L_2e62: test byte [bp-0xe],0x2
L_2e66: jz short L_2e8c
L_2e68: mov al,[bp-0x1]
L_2e6b: push ax
L_2e6c: lea ax,[bp-0xc]
L_2e6f: push ax
L_2e70: call attribute_repair_write
L_2e73: mov al,[bp-0x1]
L_2e76: mov bx,[erase_attribute_values_base]
L_2e7a: mov [bx+si],al
L_2e7c: dec word [bp-0x6]
L_2e7f: lea ax,[bp-0xc]
L_2e82: push ax
L_2e83: call attribute_repair_advance
L_2e86: inc word [bp-0x6]
L_2e89: inc si
L_2e8a: jmp short L_2e14
L_2e8c: test byte [bp-0xe],0x1
L_2e90: jz short L_2e68
L_2e92: mov al,[attributes_protected_value]
L_2e95: and al,0x7
L_2e97: mov cl,[bp-0x1]
L_2e9a: and cl,0xf8
L_2e9d: xor_load al,cl
L_2e9f: jmp short L_2e6b
L_2ea1: nop
L_2ea2: pop si
L_2ea3: pop di
L_2ea4: mov_load sp,bp
L_2ea6: pop bp
L_2ea7: ret word 0x2
