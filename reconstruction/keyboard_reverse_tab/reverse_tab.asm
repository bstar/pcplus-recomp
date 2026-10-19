; Recovered PCPlus 2.01 terminal support instructions; see docs/KEYBOARD_REVERSE_TAB.md.
BITS 16
CPU 8086
%ifdef KEYBOARD_REVERSE_TAB_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_reverse_tab
extern screen_cursor_left
extern screen_adjust_attribute_boundary
extern reverse_tab_signed_divide
extern screen_set_cursor
extern screen_cursor_right
extern reverse_tab_protected_home
extern screen_cursor_wrap
extern screen_attribute_checks
extern screen_attribute_offset
extern screen_reverse_wrap_blocked
extern screen_attributes_base
extern screen_attribute_row_bytes
extern terminal_tab_stops
extern terminal_tab_wrap
extern scroll_skip_attribute_scan
extern terminal_tab_mode_8ff8
extern screen_cursor_column
extern screen_cursor_row
%define short
%else
ORG 0xbc0
%define screen_cursor_left 0x1e30
%define screen_adjust_attribute_boundary 0x2adc
%define reverse_tab_signed_divide 0x830c
%define screen_set_cursor 0x1bbe
%define screen_cursor_right 0x1ea0
%define reverse_tab_protected_home 0x1f56
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define screen_attribute_offset 0x3346
%define screen_reverse_wrap_blocked 0x9038
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define terminal_tab_stops 0xce10
%define terminal_tab_wrap 0x903e
%define scroll_skip_attribute_scan 0x904c
%define terminal_tab_mode_8ff8 0x8ff8
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%endif
%include "encodings.inc"
keyboard_reverse_tab:
L_0bc0: push si
L_0bc1: sub_load bx,bx
L_0bc3: cmp [screen_cursor_wrap],bx
L_0bc7: jz short L_0c28
L_0bc9: cmp [screen_attribute_checks],bx
L_0bcd: jz short L_0c28
L_0bcf: call screen_cursor_left
L_0bd2: cmp word [screen_attribute_offset],0x0
L_0bd7: jnz short L_0be3
L_0bd9: cmp word [screen_reverse_wrap_blocked],0x0
L_0bde: jz short L_0be3
L_0be0: jmp near L_0ca0
L_0be3: mov bx,[screen_attribute_offset]
L_0be7: mov si,[screen_attributes_base]
L_0beb: test byte [bx+si],0x81
L_0bee: jz short L_0bf7
L_0bf0: sub_load ax,ax
L_0bf2: push ax
L_0bf3: push bx
L_0bf4: call screen_adjust_attribute_boundary
L_0bf7: mov si,[screen_attribute_offset]
L_0bfb: or_load si,si
L_0bfd: jz short L_0c0b
L_0bff: mov bx,[screen_attributes_base]
L_0c03: test byte [bx+si],0x81
L_0c06: jnz short L_0c0b
L_0c08: dec si
L_0c09: jnz short L_0bff
L_0c0b: or_load si,si
L_0c0d: jz short L_0c22
L_0c0f: push word [screen_attribute_row_bytes]
L_0c13: push si
L_0c14: call reverse_tab_signed_divide
L_0c17: add sp,0x4
L_0c1a: call screen_set_cursor
L_0c1d: call screen_cursor_right
L_0c20: pop si
L_0c21: ret
L_0c22: call reverse_tab_protected_home
L_0c25: pop si
L_0c26: ret
L_0c27: nop
L_0c28: cmp byte [terminal_tab_stops],0xfe
L_0c2d: jnz short L_0c5e
L_0c2f: cmp [terminal_tab_wrap],bx
L_0c33: jnz short L_0ca0
L_0c35: cmp [scroll_skip_attribute_scan],bx
L_0c39: jnz short L_0ca0
L_0c3b: cmp [terminal_tab_mode_8ff8],bx
L_0c3f: jnz short L_0ca0
L_0c41: cmp word [screen_cursor_column],0x0
L_0c46: jnz short L_0c98
L_0c48: cmp word [terminal_tab_wrap],0x0
L_0c4d: jnz short L_0c56
L_0c4f: cmp word [scroll_skip_attribute_scan],0x0
L_0c54: jz short L_0ca0
L_0c56: call screen_cursor_left
L_0c59: call L_0bc0
L_0c5c: pop si
L_0c5d: ret
L_0c5e: mov_load si,bx
L_0c60: inc bx
L_0c61: cmp byte [si+terminal_tab_stops],0xfe
L_0c66: jnz short L_0c5e
L_0c68: lea si,[bx-0x2]
L_0c6b: or_load si,si
L_0c6d: jl short L_0c41
L_0c6f: mov al,[screen_cursor_column]
L_0c72: cmp [si+terminal_tab_stops],al
L_0c76: jna short L_0c7e
L_0c78: dec si
L_0c79: jns short L_0c6f
L_0c7b: jmp short L_0c41
L_0c7d: nop
L_0c7e: mov al,[screen_cursor_column]
L_0c81: cmp [si+terminal_tab_stops],al
L_0c85: jnz short L_0c88
L_0c87: dec si
L_0c88: or_load si,si
L_0c8a: jl short L_0c41
L_0c8c: mov dl,[si+terminal_tab_stops]
L_0c90: sub_load dh,dh
L_0c92: mov ax,[screen_cursor_row]
L_0c95: jmp short L_0c9d
L_0c97: nop
L_0c98: mov ax,[screen_cursor_row]
L_0c9b: sub_load dx,dx
L_0c9d: call screen_set_cursor
L_0ca0: pop si
L_0ca1: ret
