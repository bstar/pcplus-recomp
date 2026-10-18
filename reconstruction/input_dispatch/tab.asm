; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_tab
extern terminal_signed_divide
extern screen_set_cursor
extern screen_cursor_right
extern screen_wrap_forward
extern screen_adjust_attribute_boundary
extern terminal_input_mode_8fe8
extern csi_wrap_pending
extern screen_cursor_wrap
extern screen_attribute_checks
extern erase_cell_count
extern screen_attribute_offset
extern screen_attributes_base
extern screen_attribute_row_bytes
extern screen_cursor_column
extern screen_cursor_row
extern screen_last_column
extern terminal_tab_wrap
extern terminal_tab_mode_8ff8
extern terminal_tab_stops
%define short
%else
ORG 0xa8c
%define terminal_signed_divide 0x830c
%define screen_set_cursor 0x1bbe
%define screen_cursor_right 0x1ea0
%define screen_wrap_forward 0x12c8
%define screen_adjust_attribute_boundary 0x2adc
%define terminal_input_mode_8fe8 0x8fe8
%define csi_wrap_pending 0x3342
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define erase_cell_count 0x325c
%define screen_attribute_offset 0x3346
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_last_column 0x3258
%define terminal_tab_wrap 0x903e
%define terminal_tab_mode_8ff8 0x8ff8
%define terminal_tab_stops 0xce10
%endif
%include "encodings.inc"
terminal_tab:
L_0a8c: push si
L_0a8d: mov word [csi_wrap_pending],0x0
L_0a93: cmp word [screen_cursor_wrap],0x0
L_0a98: jz short L_0ade
L_0a9a: cmp word [screen_attribute_checks],0x0
L_0a9f: jz short L_0ade
L_0aa1: mov dx,[erase_cell_count]
L_0aa5: mov si,[screen_attribute_offset]
L_0aa9: mov bx,[screen_attributes_base]
L_0aad: test byte [bx+si],0x81
L_0ab0: jnz short L_0aca
L_0ab2: inc si
L_0ab3: cmp_load si,dx
L_0ab5: jng short L_0aa9
L_0ab7: sub_load ax,ax
L_0ab9: cwd
L_0aba: call screen_set_cursor
L_0abd: mov ax,0x1
L_0ac0: push ax
L_0ac1: sub_load ax,ax
L_0ac3: push ax
L_0ac4: call screen_adjust_attribute_boundary
L_0ac7: pop si
L_0ac8: ret
L_0ac9: nop
L_0aca: push word [screen_attribute_row_bytes]
L_0ace: push si
L_0acf: call terminal_signed_divide
L_0ad2: add sp,0x4
L_0ad5: call screen_set_cursor
L_0ad8: call screen_cursor_right
L_0adb: pop si
L_0adc: ret
L_0add: nop
L_0ade: cmp byte [terminal_tab_stops],0xfe
L_0ae3: jz short L_0b4c
L_0ae5: sub_load si,si
L_0ae7: mov al,[screen_cursor_column]
L_0aea: cmp [si+terminal_tab_stops],al
L_0aee: jnc short L_0af8
L_0af0: inc si
L_0af1: cmp si,0x1e
L_0af4: jl short L_0ae7
L_0af6: pop si
L_0af7: ret
L_0af8: mov al,[screen_cursor_column]
L_0afb: cmp [si+terminal_tab_stops],al
L_0aff: jnz short L_0b02
L_0b01: inc si
L_0b02: cmp byte [si+terminal_tab_stops],0xfe
L_0b07: jnz short L_0b40
L_0b09: cmp word [terminal_tab_wrap],0x0
L_0b0e: jz short L_0b16
L_0b10: call screen_wrap_forward
L_0b13: pop si
L_0b14: ret
L_0b15: nop
L_0b16: cmp word [screen_cursor_wrap],0x0
L_0b1b: jnz short L_0b4c
L_0b1d: cmp word [terminal_tab_mode_8ff8],0x0
L_0b22: jnz short L_0b4c
L_0b24: cmp word [terminal_input_mode_8fe8],0x0
L_0b29: jz short L_0b38
L_0b2b: mov ax,[screen_cursor_row]
L_0b2e: mov dx,[screen_last_column]
L_0b32: call screen_set_cursor
L_0b35: pop si
L_0b36: ret
L_0b37: nop
L_0b38: mov ax,[screen_cursor_row]
L_0b3b: sub_load dx,dx
L_0b3d: jmp short L_0b32
L_0b3f: nop
L_0b40: mov dl,[si+terminal_tab_stops]
L_0b44: sub_load dh,dh
L_0b46: mov ax,[screen_cursor_row]
L_0b49: jmp short L_0b32
L_0b4b: nop
L_0b4c: pop si
L_0b4d: ret
