; Recovered PCPlus 2.01 attribute instructions; see docs/ATTRIBUTES.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTES_OMF
SEGMENT _TEXT public class=CODE use16
global attributes_normal,attributes_preset,attributes_bold,attributes_underline,attributes_blink,attributes_reverse,attributes_default_transform
extern attributes_reset
extern attributes_blink_active
extern attributes_bold_active
extern attributes_monochrome
extern attributes_current
extern attributes_reverse_active
extern attributes_color_mode
extern attributes_normal_value
extern attributes_bold_value
extern attributes_preset_value
extern attributes_reverse_value
extern attributes_underline_value
%define short
%else
ORG 0x1c8c
%define attributes_reset 0x24da
%define attributes_blink_active 0x397e
%define attributes_bold_active 0x397c
%define attributes_monochrome 0x8ff6
%define attributes_current 0x1f70
%define attributes_reverse_active 0x321c
%define attributes_color_mode 0xd122
%define attributes_normal_value 0x1d32
%define attributes_bold_value 0x1d34
%define attributes_preset_value 0x1d36
%define attributes_reverse_value 0x1d38
%define attributes_underline_value 0x1d3a
%endif
%include "encodings.inc"
attributes_normal:
L_1c8c: sub_load ax,ax
L_1c8e: mov [attributes_blink_active],ax
L_1c91: mov [attributes_bold_active],ax
L_1c94: call attributes_reset
L_1c97: cmp word [attributes_monochrome],0x0
L_1c9c: jz short L_1ca4
L_1c9e: mov word [attributes_current],0x7
L_1ca4: mov byte [attributes_reverse_active],0x0
L_1ca9: ret
attributes_preset:
L_1caa: mov ax,[attributes_preset_value]
L_1cad: mov [attributes_current],ax
L_1cb0: ret
L_1cb1: nop
attributes_bold:
L_1cb2: mov word [attributes_bold_active],0x1
L_1cb8: cmp word [attributes_color_mode],0x0
L_1cbd: jz short L_1cc6
L_1cbf: or byte [attributes_current],0x8
L_1cc4: ret
L_1cc5: nop
L_1cc6: mov ax,[attributes_bold_value]
L_1cc9: mov [attributes_current],ax
L_1ccc: ret
L_1ccd: nop
attributes_underline:
L_1cce: cmp word [attributes_monochrome],0x0
L_1cd3: jz short L_1cdc
L_1cd5: mov ax,0x1
L_1cd8: mov [attributes_current],ax
L_1cdb: ret
L_1cdc: mov ax,[attributes_underline_value]
L_1cdf: mov [attributes_current],ax
L_1ce2: ret
L_1ce3: nop
attributes_blink:
L_1ce4: or byte [attributes_current],0x80
L_1ce9: mov word [attributes_blink_active],0x1
L_1cef: ret
attributes_reverse:
L_1cf0: push bp
L_1cf1: mov_load bp,sp
L_1cf3: sub sp,0x4
L_1cf6: push di
L_1cf7: mov dl,[attributes_current]
L_1cfb: and dx,0xf
L_1cfe: mov bx,[attributes_current]
L_1d02: mov cl,0x4
L_1d04: sar bx,cl
L_1d06: mov [bp-0x2],bx
L_1d09: and bx,0x8
L_1d0c: mov_load di,dx
L_1d0e: and di,0x8
L_1d11: cmp word [attributes_color_mode],0x0
L_1d16: jz short L_1d4e
L_1d18: mov [bp-0x4],dx
L_1d1b: cmp byte [attributes_reverse_active],0x0
L_1d20: jnz short L_1d66
L_1d22: mov byte [attributes_reverse_active],0x1
L_1d27: cmp word [attributes_monochrome],0x0
L_1d2c: jz short L_1d36
L_1d2e: mov word [attributes_current],0x70
L_1d34: jmp short L_1d54
L_1d36: mov dx,[bp-0x2]
L_1d39: mov cl,0x4
L_1d3b: mov ax,[bp-0x4]
L_1d3e: shl ax,cl
L_1d40: mov [attributes_current],ax
L_1d43: or_load ax,dx
L_1d45: mov [attributes_current],ax
L_1d48: and ax,strict word 0x77
L_1d4b: jmp short L_1d51
L_1d4d: nop
L_1d4e: mov ax,[attributes_reverse_value]
L_1d51: mov [attributes_current],ax
L_1d54: or_load bx,bx
L_1d56: jz short L_1d5d
L_1d58: or byte [attributes_current],0x80
L_1d5d: or_load di,di
L_1d5f: jz short L_1d66
L_1d61: or byte [attributes_current],0x8
L_1d66: pop di
L_1d67: mov_load sp,bp
L_1d69: pop bp
L_1d6a: ret
L_1d6b: nop
attributes_default_transform:
L_1d6c: mov ax,[attributes_normal_value]
L_1d6f: or ah,0xf
L_1d72: mov cl,0x4
L_1d74: sar ax,cl
L_1d76: mov cx,[attributes_normal_value]
L_1d7a: or cl,0xf
L_1d7d: mov [attributes_current],cx
L_1d81: and_load cx,ax
L_1d83: mov [attributes_current],cx
L_1d87: ret
