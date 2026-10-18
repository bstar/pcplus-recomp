; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_set_cursor
extern screen_cursor_pack
extern screen_viewport_enter
extern screen_viewport_leave
extern screen_viewport_refresh
extern screen_viewport_enabled
extern screen_viewport_left
extern screen_viewport_active
extern screen_viewport_offset
extern screen_viewport_right
extern screen_visible_column
extern screen_video_offset
extern screen_previous_column
extern screen_attribute_offset
extern screen_cursor_column
extern screen_previous_row
extern screen_video_row_bytes
extern screen_attribute_row_bytes
extern screen_cursor_row
%define short
%else
ORG 0x1bbe
%define screen_cursor_pack 0x6e66
%define screen_viewport_enter 0x482a
%define screen_viewport_leave 0x4850
%define screen_viewport_refresh 0x2fb8
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_left 0xce2e
%define screen_viewport_active 0x3256
%define screen_viewport_offset 0x39a4
%define screen_viewport_right 0x7a7e
%define screen_visible_column 0x39a0
%define screen_video_offset 0x3344
%define screen_previous_column 0x3348
%define screen_attribute_offset 0x3346
%define screen_cursor_column 0x399e
%define screen_previous_row 0x39a2
%define screen_video_row_bytes 0x7a7a
%define screen_attribute_row_bytes 0x325a
%define screen_cursor_row 0x399c
%endif
%include "encodings.inc"
screen_set_cursor:
L_1bbe: push di
L_1bbf: push si
L_1bc0: mov_load di,ax
L_1bc2: mov_load si,dx
L_1bc4: cmp word [screen_viewport_enabled],0x0
L_1bc9: jz short L_1c09
L_1bcb: cmp [screen_viewport_left],si
L_1bcf: jna short L_1bea
L_1bd1: cmp word [screen_viewport_active],0x0
L_1bd6: jnz short L_1bea
L_1bd8: call screen_viewport_enter
L_1bdb: mov word [screen_viewport_active],0x1
L_1be1: mov word [screen_viewport_offset],0x0
L_1be7: jmp short L_1c06
L_1be9: nop
L_1bea: cmp [screen_viewport_right],si
L_1bee: jnl short L_1c09
L_1bf0: cmp word [screen_viewport_active],0x0
L_1bf5: jz short L_1c09
L_1bf7: call screen_viewport_leave
L_1bfa: mov word [screen_viewport_active],0x0
L_1c00: mov ax,[screen_viewport_left]
L_1c03: mov [screen_viewport_offset],ax
L_1c06: call screen_viewport_refresh
L_1c09: mov_load ax,si
L_1c0b: sub si,[screen_viewport_offset]
L_1c0f: mov_load cx,si
L_1c11: sub si,[screen_visible_column]
L_1c15: shl si,1
L_1c17: add [screen_video_offset],si
L_1c1b: mov [screen_visible_column],cx
L_1c1f: mov_load cx,ax
L_1c21: mov_load dx,ax
L_1c23: sub ax,[screen_previous_column]
L_1c27: add [screen_attribute_offset],ax
L_1c2b: mov [screen_cursor_column],cx
L_1c2f: mov [screen_previous_column],dx
L_1c33: cmp [screen_previous_row],di
L_1c37: jz short L_1c57
L_1c39: mov_load ax,di
L_1c3b: sub ax,[screen_previous_row]
L_1c3f: mov_load cx,ax
L_1c41: imul word [screen_video_row_bytes]
L_1c45: add [screen_video_offset],ax
L_1c49: mov_load ax,cx
L_1c4b: mul word [screen_attribute_row_bytes]
L_1c4f: add [screen_attribute_offset],ax
L_1c53: mov [screen_previous_row],di
L_1c57: mov [screen_cursor_row],di
L_1c5b: push di
L_1c5c: push word [screen_visible_column]
L_1c60: call screen_cursor_pack
L_1c63: pop si
L_1c64: pop di
L_1c65: ret
