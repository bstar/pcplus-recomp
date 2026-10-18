; Recovered PCPlus 2.01 high-level character instructions; see docs/RENDER.md.
BITS 16
CPU 8086
%ifdef RENDER_OMF
SEGMENT _TEXT public class=CODE use16
global render_character
extern scroll_up
extern screen_set_cursor
extern render_service_b9f7
extern text_write_packed
extern text_fill_cells
extern screen_adjust_attribute_boundary
extern text_write_char
extern render_font_output
extern erase_repair_attributes
extern erase_previous_attribute
extern text_write_cell
extern csi_wrap_pending
extern render_autowrap
extern screen_cursor_row
extern render_deferred_row
extern screen_cursor_column
extern render_deferred_column
extern screen_last_row
extern scroll_enabled
extern csi_last_row
extern terminal_mode_372c
extern attributes_color_mode
extern ansi_charset_g0_flag_a
extern cursor_state_value_cdfc
extern ansi_charset_g1_flag_a
extern cursor_state_value_ce04
extern ansi_charset_g1_flag_graphics
extern ansi_charset_g0_flag_graphics
extern render_graphics_map
extern screen_line_flags
extern attributes_current
extern screen_video_offset
extern screen_cursor_wrap
extern scroll_suppress_next_linefeed
extern render_translation_enabled
extern render_translation_mask
extern render_translation_base
extern render_direct_output
extern screen_attribute_offset
extern screen_attribute_checks
extern screen_attributes_base
extern erase_protection_mode
extern screen_last_column
extern render_linefeed_suppression_enabled
%define short
%else
ORG 0x730
%define scroll_up 0x1fc4
%define screen_set_cursor 0x1bbe
%define render_service_b9f7 0xb9f7
%define text_write_packed 0x6cb4
%define text_fill_cells 0x6c20
%define screen_adjust_attribute_boundary 0x2adc
%define text_write_char 0x6c84
%define render_font_output 0xbb53
%define erase_repair_attributes 0x2d98
%define erase_previous_attribute 0x2d4c
%define text_write_cell 0x6c5e
%define csi_wrap_pending 0x3342
%define render_autowrap 0x1d20
%define screen_cursor_row 0x399c
%define render_deferred_row 0xd116
%define screen_cursor_column 0x399e
%define render_deferred_column 0xd120
%define screen_last_row 0xce3a
%define scroll_enabled 0x1d22
%define csi_last_row 0x334a
%define terminal_mode_372c 0x372c
%define attributes_color_mode 0xd122
%define ansi_charset_g0_flag_a 0xcde0
%define cursor_state_value_cdfc 0xcdfc
%define ansi_charset_g1_flag_a 0xcde8
%define cursor_state_value_ce04 0xce04
%define ansi_charset_g1_flag_graphics 0xcdf0
%define ansi_charset_g0_flag_graphics 0xcdec
%define render_graphics_map 0x459b
%define screen_line_flags 0xcf86
%define attributes_current 0x1f70
%define screen_video_offset 0x3344
%define screen_cursor_wrap 0x900c
%define scroll_suppress_next_linefeed 0x3340
%define render_translation_enabled 0x372e
%define render_translation_mask 0x902d
%define render_translation_base 0x9036
%define render_direct_output 0x9056
%define screen_attribute_offset 0x3346
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define erase_protection_mode 0x3736
%define screen_last_column 0x3258
%define render_linefeed_suppression_enabled 0x9004
%endif
%include "encodings.inc"
render_character:
L_0730: push bp
L_0731: mov_load bp,sp
L_0733: push di
L_0734: push si
L_0735: cmp word [csi_wrap_pending],0x0
L_073a: jz short L_0780
L_073c: mov word [csi_wrap_pending],0x0
L_0742: cmp word [render_autowrap],0x0
L_0747: jz short L_0780
L_0749: mov ax,[screen_cursor_row]
L_074c: cmp [render_deferred_row],ax
L_0750: jnz short L_0780
L_0752: mov ax,[screen_cursor_column]
L_0755: cmp [render_deferred_column],ax
L_0759: jnz short L_0780
L_075b: mov ax,[screen_cursor_row]
L_075e: cmp [screen_last_row],ax
L_0762: jnz short L_0774
L_0764: cmp word [scroll_enabled],0x0
L_0769: jz short L_076e
L_076b: call scroll_up
L_076e: mov ax,[screen_last_row]
L_0771: jmp short L_077b
L_0773: nop
L_0774: cmp [csi_last_row],ax
L_0778: jz short L_077b
L_077a: inc ax
L_077b: sub_load dx,dx
L_077d: call screen_set_cursor
L_0780: cmp word [terminal_mode_372c],0x0
L_0785: jz short L_078a
L_0787: call render_service_b9f7
L_078a: cmp word [attributes_color_mode],0x0
L_078f: jnz short L_0794
L_0791: jmp near L_0834
L_0794: mov si,[bp+0x4]
L_0797: cmp si,0x23
L_079a: jnz short L_07be
L_079c: cmp word [ansi_charset_g0_flag_a],0x0
L_07a1: jz short L_07aa
L_07a3: cmp word [cursor_state_value_cdfc],0x0
L_07a8: jnz short L_07b8
L_07aa: cmp word [ansi_charset_g1_flag_a],0x0
L_07af: jz short L_07eb
L_07b1: cmp word [cursor_state_value_ce04],0x0
L_07b6: jz short L_07eb
L_07b8: mov si,0xff9c
L_07bb: jmp short L_07eb
L_07bd: nop
L_07be: cmp word [cursor_state_value_ce04],0x0
L_07c3: jz short L_07cc
L_07c5: cmp word [ansi_charset_g1_flag_graphics],0x0
L_07ca: jnz short L_07da
L_07cc: cmp word [cursor_state_value_cdfc],0x0
L_07d1: jz short L_07eb
L_07d3: cmp word [ansi_charset_g0_flag_graphics],0x0
L_07d8: jz short L_07eb
L_07da: cmp si,0x5e
L_07dd: jng short L_07eb
L_07df: cmp si,0x7f
L_07e2: jnl short L_07eb
L_07e4: mov al,[si+render_graphics_map]
L_07e8: cbw
L_07e9: mov_load si,ax
L_07eb: mov bx,[screen_cursor_row]
L_07ef: test byte [bx+screen_line_flags],0x40
L_07f4: jz short L_082e
L_07f6: test byte [bx+screen_line_flags],0x2
L_07fb: jz short L_0802
L_07fd: mov di,0x2
L_0800: jmp short L_0817
L_0802: mov di,0x1
L_0805: mov_load ax,si
L_0807: mov cl,[attributes_current]
L_080b: mov_load ch,al
L_080d: push cx
L_080e: mov ax,[screen_video_offset]
L_0811: inc ax
L_0812: inc ax
L_0813: push ax
L_0814: call text_write_packed
L_0817: mov ax,[attributes_current]
L_081a: or ah,0x20
L_081d: push ax
L_081e: push word [screen_video_offset]
L_0822: push di
L_0823: call text_fill_cells
L_0826: inc word [screen_cursor_column]
L_082a: jmp near L_0921
L_082d: nop
L_082e: mov_load ax,si
L_0830: jmp near L_0915
L_0833: nop
L_0834: cmp word [screen_cursor_wrap],0x0
L_0839: jnz short L_083e
L_083b: jmp near L_0912
L_083e: mov word [scroll_suppress_next_linefeed],0x0
L_0844: mov di,[bp+0x4]
L_0847: cmp word [render_translation_enabled],0x0
L_084c: jz short L_085e
L_084e: mov al,[render_translation_mask]
L_0851: sub_load ah,ah
L_0853: and_load di,ax
L_0855: mov bx,[render_translation_base]
L_0859: mov al,[bx+di]
L_085b: cbw
L_085c: mov_load di,ax
L_085e: cmp word [render_direct_output],0x0
L_0863: jz short L_0868
L_0865: jmp near L_090e
L_0868: mov si,[screen_attribute_offset]
L_086c: cmp word [screen_attribute_checks],0x0
L_0871: jz short L_08b8
L_0873: mov bx,[screen_attributes_base]
L_0877: test byte [bx+si],0x81
L_087a: jz short L_0888
L_087c: mov ax,0x1
L_087f: push ax
L_0880: push si
L_0881: call screen_adjust_attribute_boundary
L_0884: mov si,[screen_attribute_offset]
L_0888: mov bx,[screen_attributes_base]
L_088c: test byte [bx+si],0x81
L_088f: jz short L_0894
L_0891: jmp near L_0921
L_0894: cmp word [erase_protection_mode],0x0
L_0899: jnz short L_08ae
L_089b: cmp word [render_translation_enabled],0x0
L_08a0: jnz short L_08ae
L_08a2: push di
L_08a3: push word [screen_video_offset]
L_08a7: call text_write_char
L_08aa: jmp short L_0921
L_08ac: nop
L_08ad: nop
L_08ae: mov_load ax,di
L_08b0: push ax
L_08b1: push si
L_08b2: call render_font_output
L_08b5: jmp short L_0921
L_08b7: nop
L_08b8: mov bx,[screen_attributes_base]
L_08bc: test byte [bx+si],0x80
L_08bf: jz short L_08cb
L_08c1: and byte [bx+si],0x7f
L_08c4: mov ax,0x2
L_08c7: push ax
L_08c8: call erase_repair_attributes
L_08cb: cmp word [erase_protection_mode],0x0
L_08d0: jnz short L_08ae
L_08d2: cmp word [render_translation_enabled],0x0
L_08d7: jnz short L_08ea
L_08d9: mov bx,[screen_attributes_base]
L_08dd: test byte [bx+si],0x3
L_08e0: jnz short L_08ea
L_08e2: mov_load ax,di
L_08e4: sub_load ah,ah
L_08e6: push ax
L_08e7: jmp short L_08a3
L_08e9: nop
L_08ea: cmp word [render_translation_enabled],0x0
L_08ef: jz short L_08fa
L_08f1: mov bx,[screen_attributes_base]
L_08f5: or byte [bx+si],0x3
L_08f8: jmp short L_0901
L_08fa: mov bx,[screen_attributes_base]
L_08fe: and byte [bx+si],0xfc
L_0901: mov_load ax,di
L_0903: push ax
L_0904: push si
L_0905: call erase_previous_attribute
L_0908: sub_load ah,ah
L_090a: push ax
L_090b: jmp short L_091a
L_090d: nop
L_090e: mov_load ax,di
L_0910: jmp short L_0915
L_0912: mov al,[bp+0x4]
L_0915: push ax
L_0916: push word [attributes_current]
L_091a: push word [screen_video_offset]
L_091e: call text_write_cell
L_0921: mov ax,[screen_last_column]
L_0924: cmp [screen_cursor_column],ax
L_0928: jnc short L_0934
L_092a: mov dx,[screen_cursor_column]
L_092e: inc dx
L_092f: mov ax,[screen_cursor_row]
L_0932: jmp short L_0991
L_0934: cmp word [render_autowrap],0x0
L_0939: jz short L_0994
L_093b: cmp word [attributes_color_mode],0x0
L_0940: jz short L_0956
L_0942: mov word [csi_wrap_pending],0x1
L_0948: mov ax,[screen_cursor_row]
L_094b: mov [render_deferred_row],ax
L_094e: mov ax,[screen_cursor_column]
L_0951: mov [render_deferred_column],ax
L_0954: jmp short L_0994
L_0956: cmp word [render_linefeed_suppression_enabled],0x0
L_095b: jz short L_096a
L_095d: cmp word [screen_attribute_checks],0x0
L_0962: jnz short L_096a
L_0964: mov word [scroll_suppress_next_linefeed],0x1
L_096a: mov ax,[screen_cursor_row]
L_096d: cmp [screen_last_row],ax
L_0971: jg short L_098e
L_0973: cmp word [scroll_enabled],0x0
L_0978: jz short L_0982
L_097a: call scroll_up
L_097d: mov ax,[screen_last_row]
L_0980: jmp short L_098f
L_0982: cmp word [screen_cursor_wrap],0x0
L_0987: jz short L_097d
L_0989: sub_load ax,ax
L_098b: jmp short L_098f
L_098d: nop
L_098e: inc ax
L_098f: sub_load dx,dx
L_0991: call screen_set_cursor
L_0994: cmp word [screen_attribute_checks],0x0
L_0999: jz short L_09b0
L_099b: mov si,[screen_attribute_offset]
L_099f: mov bx,[screen_attributes_base]
L_09a3: test byte [bx+si],0x81
L_09a6: jz short L_09b0
L_09a8: mov ax,0x1
L_09ab: push ax
L_09ac: push si
L_09ad: call screen_adjust_attribute_boundary
L_09b0: pop si
L_09b1: pop di
L_09b2: mov_load sp,bp
L_09b4: pop bp
L_09b5: ret
