; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_BOUNDARY.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_BOUNDARY_OMF
%ifdef KEYBOARD_ECHO_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_boundary_native
extern attribute_offset_to_position
extern screen_set_cursor
extern attribute_boundary_notice
extern screen_attributes_base
extern erase_cell_count
%define short
%else
ORG 0x2adc
%define attribute_offset_to_position 0x2bde
%define screen_set_cursor 0x1bbe
%define attribute_boundary_notice 0x376d
%define screen_attributes_base 0x39c4
%define erase_cell_count 0x325c
%endif
%include "encodings.inc"
attribute_boundary_native:
L_2adc: push bp
L_2add: mov_load bp,sp
L_2adf: sub sp,0xc
L_2ae2: push di
L_2ae3: push si
L_2ae4: mov dx,[bp+0x6]
L_2ae7: mov word [bp-0x4],0x0
L_2aec: mov si,[bp+0x4]
L_2aef: cmp dx,0x1
L_2af2: sbb_load ax,ax
L_2af4: and al,0xfe
L_2af6: inc ax
L_2af7: mov [bp-0x2],ax
L_2afa: mov bx,[screen_attributes_base]
L_2afe: test byte [bx+si],0x81
L_2b01: jz short L_2b18
L_2b03: mov_load bx,ax
L_2b05: cmp [erase_cell_count],si
L_2b09: jna short L_2b18
L_2b0b: add_load si,bx
L_2b0d: mov_load di,si
L_2b0f: add di,[screen_attributes_base]
L_2b13: test byte [di],0x81
L_2b16: jnz short L_2b05
L_2b18: cmp [erase_cell_count],si
L_2b1c: ja short L_2b51
L_2b1e: mov word [bp-0x4],0x1
L_2b23: or_load dx,dx
L_2b25: jz short L_2b2c
L_2b27: sub_load si,si
L_2b29: jmp short L_2b31
L_2b2b: nop
L_2b2c: mov si,[erase_cell_count]
L_2b30: dec si
L_2b31: mov bx,[screen_attributes_base]
L_2b35: test byte [bx+si],0x81
L_2b38: jz short L_2b51
L_2b3a: mov bx,[bp-0x2]
L_2b3d: mov dx,[bp+0x4]
L_2b40: cmp_load si,dx
L_2b42: jz short L_2b51
L_2b44: add_load si,bx
L_2b46: mov_load di,si
L_2b48: add di,[screen_attributes_base]
L_2b4c: test byte [di],0x81
L_2b4f: jnz short L_2b40
L_2b51: cmp [bp+0x4],si
L_2b54: jnz short L_2b6a
L_2b56: cmp word [bp-0x4],0x0
L_2b5a: jz short L_2b65
L_2b5c: call attribute_boundary_notice
L_2b5f: sub_load ax,ax
L_2b61: cwd
L_2b62: call screen_set_cursor
L_2b65: sub_load ax,ax
L_2b67: jmp short L_2b7e
L_2b69: nop
L_2b6a: push si
L_2b6b: lea ax,[bp-0xc]
L_2b6e: push ax
L_2b6f: call attribute_offset_to_position
L_2b72: mov ax,[bp-0xa]
L_2b75: mov dx,[bp-0x8]
L_2b78: call screen_set_cursor
L_2b7b: mov ax,0x1
L_2b7e: pop si
L_2b7f: pop di
L_2b80: mov_load sp,bp
L_2b82: pop bp
L_2b83: ret word 0x4
