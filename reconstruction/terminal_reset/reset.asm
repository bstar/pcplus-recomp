; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_native
extern terminal_reset_bios_rectangle
extern terminal_reset_clear_video
extern terminal_reset_clear_shadow
extern terminal_reset_cursor_default
extern terminal_reset_protected_home
extern terminal_reset_status_fill
extern terminal_reset_underline_default
extern terminal_reset_underline_configured
extern terminal_reset_geometry
extern terminal_reset_status_refresh
extern screen_set_cursor
extern terminal_keyboard_mode
extern terminal_reset_load_keymap
extern terminal_clear_home
extern csi_clear_tabs
extern terminal_reset_input_attribute
extern terminal_reset_input_plain
extern screen_viewport_right
extern screen_cursor_column
extern screen_attribute_row_bytes
extern screen_cursor_row
extern screen_top_margin
extern screen_doublewidth_enabled
extern screen_last_row
extern screen_vertical_attribute_check
extern screen_attribute_checks
extern screen_attributes_base
extern screen_bottom_margin
extern screen_line_flags
extern screen_cursor_wrap
extern screen_first_row
extern screen_reverse_wrap_blocked
extern program_state_7a72
extern attributes_blink_active
extern attributes_monochrome
extern attributes_current
extern attributes_reverse_active
extern attributes_normal_value
extern erase_lineflags_enabled
extern erase_protection_mode
extern erase_attribute_values_base
extern csi_last_row
extern csi_erase_attribute
extern scroll_enabled
extern terminal_keymap_end
extern ansi_charset_g0_flag_a
extern cursor_state_value_cdfc
extern ansi_charset_g1_flag_a
extern cursor_state_value_ce04
extern ansi_charset_g1_flag_graphics
extern ansi_charset_g0_flag_graphics
extern scroll_suppress_next_linefeed
extern render_translation_enabled
extern render_translation_mask
extern render_translation_base
extern render_direct_output
extern render_linefeed_suppression_enabled
extern scroll_skip_attribute_scan
extern terminal_dec_keys
extern csi_terminal_id
extern terminal_tab_wrap
extern terminal_tab_mode_8ff8
extern terminal_backspace_mode_9058
extern reset_duplex
extern terminal_newline_mode_9020
extern terminal_control_mode_9026
extern reset_status_hidden
extern reset_wide_mode
extern reset_underline_enabled
extern reset_configured_wide
extern reset_saved_scroll
extern reset_saved_duplex
extern reset_scratch
extern reset_data_cd36
extern reset_data_9032
extern reset_data_9048
extern reset_data_3350
extern reset_data_334e
extern reset_data_cd84
extern reset_data_399a
extern reset_data_cd2c
extern reset_data_3732
extern reset_data_3730
extern reset_data_cdd2
extern reset_data_3982
extern reset_data_cc9e
extern reset_data_3980
extern reset_data_cd24
extern reset_data_d004
extern reset_data_cdd4
extern reset_data_462c
extern reset_data_cb30
extern reset_data_7a80
%define short
%else
ORG 0x20a4
%define terminal_reset_bios_rectangle 0x6edc
%define terminal_reset_clear_video 0x6f60
%define terminal_reset_clear_shadow 0x27ea
%define terminal_reset_cursor_default 0x2518
%define terminal_reset_protected_home 0x1f56
%define terminal_reset_status_fill 0x4097
%define terminal_reset_underline_default 0x40c9
%define terminal_reset_underline_configured 0x40df
%define terminal_reset_geometry 0x281c
%define terminal_reset_status_refresh 0x2fb8
%define screen_set_cursor 0x1bbe
%define terminal_keyboard_mode 0xb4e
%define terminal_reset_load_keymap 0xcd2
%define terminal_clear_home 0x24e2
%define csi_clear_tabs 0x246c
%define terminal_reset_input_attribute 0xbb8f
%define terminal_reset_input_plain 0xbb9b
%define screen_viewport_right 0x7a7e
%define screen_cursor_column 0x399e
%define screen_attribute_row_bytes 0x325a
%define screen_cursor_row 0x399c
%define screen_top_margin 0xceb0
%define screen_doublewidth_enabled 0xd122
%define screen_last_row 0xce3a
%define screen_vertical_attribute_check 0x9018
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define screen_bottom_margin 0xcee4
%define screen_line_flags 0xcf86
%define screen_cursor_wrap 0x900c
%define screen_first_row 0xce0e
%define screen_reverse_wrap_blocked 0x9038
%define program_state_7a72 0x7a72
%define attributes_blink_active 0x397e
%define attributes_monochrome 0x8ff6
%define attributes_current 0x1f70
%define attributes_reverse_active 0x321c
%define attributes_normal_value 0x1d32
%define erase_lineflags_enabled 0x3260
%define erase_protection_mode 0x3736
%define erase_attribute_values_base 0x39c2
%define csi_last_row 0x334a
%define csi_erase_attribute 0xd008
%define scroll_enabled 0x1d22
%define terminal_keymap_end 0x372c
%define ansi_charset_g0_flag_a 0xcde0
%define cursor_state_value_cdfc 0xcdfc
%define ansi_charset_g1_flag_a 0xcde8
%define cursor_state_value_ce04 0xce04
%define ansi_charset_g1_flag_graphics 0xcdf0
%define ansi_charset_g0_flag_graphics 0xcdec
%define scroll_suppress_next_linefeed 0x3340
%define render_translation_enabled 0x372e
%define render_translation_mask 0x902d
%define render_translation_base 0x9036
%define render_direct_output 0x9056
%define render_linefeed_suppression_enabled 0x9004
%define scroll_skip_attribute_scan 0x904c
%define terminal_dec_keys 0x8fe8
%define csi_terminal_id 0x1d18
%define terminal_tab_wrap 0x903e
%define terminal_tab_mode_8ff8 0x8ff8
%define terminal_backspace_mode_9058 0x9058
%define reset_duplex 0x1d26
%define terminal_newline_mode_9020 0x9020
%define terminal_control_mode_9026 0x9026
%define reset_status_hidden 0x1d46
%define reset_wide_mode 0x3254
%define reset_underline_enabled 0x1d2c
%define reset_configured_wide 0x1d2e
%define reset_saved_scroll 0x9016
%define reset_saved_duplex 0x903c
%define reset_scratch 0xcc4a
%define reset_data_cd36 0xcd36
%define reset_data_9032 0x9032
%define reset_data_9048 0x9048
%define reset_data_3350 0x3350
%define reset_data_334e 0x334e
%define reset_data_cd84 0xcd84
%define reset_data_399a 0x399a
%define reset_data_cd2c 0xcd2c
%define reset_data_3732 0x3732
%define reset_data_3730 0x3730
%define reset_data_cdd2 0xcdd2
%define reset_data_3982 0x3982
%define reset_data_cc9e 0xcc9e
%define reset_data_3980 0x3980
%define reset_data_cd24 0xcd24
%define reset_data_d004 0xd004
%define reset_data_cdd4 0xcdd4
%define reset_data_462c 0x462c
%define reset_data_cb30 0xcb30
%define reset_data_7a80 0x7a80
%endif
%include "encodings.inc"
terminal_reset_native:
L_20a4: push bp
L_20a5: mov_load bp,sp
L_20a7: sub sp,0x4
L_20aa: push di
L_20ab: push si
L_20ac: mov si,[bp+0x4]
L_20af: or_load si,si
L_20b1: jnz short L_20b6
L_20b3: jmp near L_23a8
L_20b6: push word [attributes_normal_value]
L_20ba: call terminal_reset_clear_video
L_20bd: call terminal_reset_clear_shadow
L_20c0: cmp word [csi_terminal_id],0x1
L_20c5: jl short L_20d6
L_20c7: cmp word [csi_terminal_id],0xb
L_20cc: jg short L_20d6
L_20ce: mov word [screen_doublewidth_enabled],0x1
L_20d4: jmp short L_20dc
L_20d6: mov word [screen_doublewidth_enabled],0x0
L_20dc: cmp word [csi_terminal_id],0x2
L_20e1: jl short L_20f2
L_20e3: cmp word [csi_terminal_id],0xb
L_20e8: jg short L_20f2
L_20ea: mov word [terminal_dec_keys],0x1
L_20f0: jmp short L_20f8
L_20f2: mov word [terminal_dec_keys],0x0
L_20f8: cmp word [csi_terminal_id],0x6
L_20fd: jl short L_210e
L_20ff: cmp word [csi_terminal_id],0x7
L_2104: jg short L_210e
L_2106: mov word [attributes_monochrome],0x1
L_210c: jmp short L_2114
L_210e: mov word [attributes_monochrome],0x0
L_2114: cmp word [csi_terminal_id],0xd
L_2119: jl short L_212a
L_211b: cmp word [csi_terminal_id],0xe
L_2120: jg short L_212a
L_2122: mov word [terminal_tab_mode_8ff8],0x1
L_2128: jmp short L_2130
L_212a: mov word [terminal_tab_mode_8ff8],0x0
L_2130: cmp word [csi_terminal_id],0x16
L_2135: jl short L_2146
L_2137: cmp word [csi_terminal_id],0x1e
L_213c: jg short L_2146
L_213e: mov word [render_linefeed_suppression_enabled],0x1
L_2144: jmp short L_214c
L_2146: mov word [render_linefeed_suppression_enabled],0x0
L_214c: cmp word [csi_terminal_id],0x19
L_2151: jl short L_2162
L_2153: cmp word [csi_terminal_id],0x1c
L_2158: jg short L_2162
L_215a: mov word [reset_data_cd36],0x1
L_2160: jmp short L_2168
L_2162: mov word [reset_data_cd36],0x0
L_2168: cmp word [csi_terminal_id],0x16
L_216d: jl short L_217e
L_216f: cmp word [csi_terminal_id],0x1d
L_2174: jg short L_217e
L_2176: mov word [screen_reverse_wrap_blocked],0x1
L_217c: jmp short L_2184
L_217e: mov word [screen_reverse_wrap_blocked],0x0
L_2184: cmp word [csi_terminal_id],0x16
L_2189: jl short L_219a
L_218b: cmp word [csi_terminal_id],0x20
L_2190: jg short L_219a
L_2192: mov word [screen_cursor_wrap],0x1
L_2198: jmp short L_21a0
L_219a: mov word [screen_cursor_wrap],0x0
L_21a0: cmp word [csi_terminal_id],0x1f
L_21a5: jl short L_21b6
L_21a7: cmp word [csi_terminal_id],0x20
L_21ac: jg short L_21b6
L_21ae: mov word [screen_vertical_attribute_check],0x1
L_21b4: jmp short L_21bc
L_21b6: mov word [screen_vertical_attribute_check],0x0
L_21bc: cmp word [csi_terminal_id],0xf
L_21c1: jl short L_21d2
L_21c3: cmp word [csi_terminal_id],0x11
L_21c8: jg short L_21d2
L_21ca: mov word [terminal_newline_mode_9020],0x1
L_21d0: jmp short L_21d8
L_21d2: mov word [terminal_newline_mode_9020],0x0
L_21d8: cmp word [csi_terminal_id],0x12
L_21dd: jl short L_21ee
L_21df: cmp word [csi_terminal_id],0x13
L_21e4: jg short L_21ee
L_21e6: mov word [terminal_control_mode_9026],0x1
L_21ec: jmp short L_21f4
L_21ee: mov word [terminal_control_mode_9026],0x0
L_21f4: cmp word [csi_terminal_id],0x14
L_21f9: jl short L_220a
L_21fb: cmp word [csi_terminal_id],0x15
L_2200: jg short L_220a
L_2202: mov word [reset_data_9032],0x1
L_2208: jmp short L_2210
L_220a: mov word [reset_data_9032],0x0
L_2210: cmp word [csi_terminal_id],0x1f
L_2215: jz short L_2226
L_2217: cmp word [csi_terminal_id],0x16
L_221c: jz short L_2226
L_221e: mov word [terminal_tab_wrap],0x0
L_2224: jmp short L_222c
L_2226: mov word [terminal_tab_wrap],0x1
L_222c: cmp word [csi_terminal_id],0x1d
L_2231: jnz short L_2238
L_2233: mov ax,0x1
L_2236: jmp short L_223a
L_2238: sub_load ax,ax
L_223a: mov [reset_data_9048],ax
L_223d: cmp word [csi_terminal_id],0x1e
L_2242: jnz short L_224a
L_2244: mov ax,0x1
L_2247: jmp short L_224c
L_2249: nop
L_224a: sub_load ax,ax
L_224c: mov [scroll_skip_attribute_scan],ax
L_224f: cmp word [csi_terminal_id],0x18
L_2254: jnz short L_225c
L_2256: mov ax,0x1
L_2259: jmp short L_225e
L_225b: nop
L_225c: sub_load ax,ax
L_225e: mov [render_direct_output],ax
L_2261: cmp word [screen_cursor_wrap],0x0
L_2266: jnz short L_227e
L_2268: cmp word [reset_data_9032],0x0
L_226d: jnz short L_227e
L_226f: cmp word [terminal_newline_mode_9020],0x0
L_2274: jnz short L_227e
L_2276: mov word [terminal_backspace_mode_9058],0x1
L_227c: jmp short L_2284
L_227e: mov word [terminal_backspace_mode_9058],0x0
L_2284: call terminal_reset_load_keymap
L_2287: sub_load ax,ax
L_2289: mov [reset_data_3350],ax
L_228c: mov [reset_data_334e],ax
L_228f: mov [attributes_blink_active],ax
L_2292: mov [reset_data_cd84],ax
L_2295: mov [screen_top_margin],ax
L_2298: mov [screen_first_row],ax
L_229b: mov [reset_data_399a],ax
L_229e: mov [ansi_charset_g1_flag_graphics],ax
L_22a1: mov [erase_lineflags_enabled],ax
L_22a4: mov [reset_data_cd2c],ax
L_22a7: mov [ansi_charset_g0_flag_graphics],ax
L_22aa: mov [reset_data_3732],ax
L_22ad: mov [erase_protection_mode],ax
L_22b0: mov [screen_attribute_checks],ax
L_22b3: mov [reset_data_3730],ax
L_22b6: mov [render_translation_enabled],ax
L_22b9: mov [terminal_keymap_end],ax
L_22bc: mov [scroll_suppress_next_linefeed],ax
L_22bf: mov [cursor_state_value_ce04],ax
L_22c2: mov [reset_data_cdd2],ax
L_22c5: mov [ansi_charset_g1_flag_a],ax
L_22c8: mov [ansi_charset_g0_flag_a],ax
L_22cb: mov [reset_data_3982],ax
L_22ce: mov byte [attributes_reverse_active],0x0
L_22d3: mov byte [reset_data_cc9e],0x0
L_22d8: mov dx,reset_scratch
L_22db: mov cx,0x48
L_22de: mov_load di,dx
L_22e0: push ds
L_22e1: pop es
L_22e2: rep stosb
L_22e4: mov ax,0x1
L_22e7: mov [reset_data_3980],ax
L_22ea: mov [cursor_state_value_cdfc],ax
L_22ed: mov [reset_data_cd24],ax
L_22f0: mov ax,[reset_saved_scroll]
L_22f3: mov [scroll_enabled],ax
L_22f6: mov [reset_data_d004],ax
L_22f9: mov ax,[attributes_normal_value]
L_22fc: mov [attributes_current],ax
L_22ff: mov [reset_data_cdd4],ax
L_2302: mov [csi_erase_attribute],al
L_2305: mov cx,[csi_last_row]
L_2309: mov [screen_bottom_margin],cx
L_230d: mov [screen_last_row],cx
L_2311: mov cl,[reset_saved_duplex]
L_2315: mov [reset_duplex],cl
L_2319: mov cx,0x64
L_231c: mov_load dx,ax
L_231e: sub_load ax,ax
L_2320: mov bx,screen_line_flags
L_2323: mov_load di,bx
L_2325: rep stosb
L_2327: mov_load al,dl
L_2329: sub_load ah,ah
L_232b: mov dx,[erase_attribute_values_base]
L_232f: mov cx,0xc60
L_2332: mov_load di,dx
L_2334: rep stosb
L_2336: sub_load ax,ax
L_2338: mov dx,[screen_attributes_base]
L_233c: mov cx,0xc60
L_233f: mov_load di,dx
L_2341: rep stosb
L_2343: mov ax,0x5b
L_2346: push ax
L_2347: call terminal_keyboard_mode
L_234a: add sp,0x2
L_234d: call terminal_reset_cursor_default
L_2350: mov word [render_translation_base],0x461c
L_2356: mov byte [render_translation_mask],0xf
L_235b: mov byte [reset_data_462c],0x20
L_2360: cmp word [scroll_skip_attribute_scan],0x0
L_2365: jz short L_2377
L_2367: mov word [reset_data_cdd2],0x1
L_236d: mov byte [render_translation_mask],0x1f
L_2372: mov byte [reset_data_462c],0x2d
L_2377: cmp word [terminal_tab_wrap],0x0
L_237c: jz short L_2389
L_237e: mov byte [render_translation_mask],0x1f
L_2383: mov word [render_translation_base],0x463e
L_2389: cmp word [screen_cursor_wrap],0x0
L_238e: jz short L_23a2
L_2390: mov word [reset_data_cb30],terminal_reset_input_attribute
L_2396: mov ax,0x17
L_2399: mov [screen_bottom_margin],ax
L_239c: mov [screen_last_row],ax
L_239f: jmp short L_23a8
L_23a1: nop
L_23a2: mov word [reset_data_cb30],terminal_reset_input_plain
L_23a8: or_load si,si
L_23aa: jnz short L_23c7
L_23ac: cmp [terminal_tab_wrap],si
L_23b0: jz short L_23c4
L_23b2: mov ax,[screen_cursor_row]
L_23b5: mov [bp-0x4],ax
L_23b8: mov ax,[screen_cursor_column]
L_23bb: mov [bp-0x2],ax
L_23be: call terminal_reset_protected_home
L_23c1: jmp short L_23c7
L_23c3: nop
L_23c4: call terminal_clear_home
L_23c7: cmp word [terminal_dec_keys],0x0
L_23cc: jnz short L_23e2
L_23ce: cmp word [terminal_tab_wrap],0x0
L_23d3: jnz short L_23e2
L_23d5: cmp word [scroll_skip_attribute_scan],0x0
L_23da: jnz short L_23e2
L_23dc: push si
L_23dd: sub_load ax,ax
L_23df: push ax
L_23e0: jmp short L_23e7
L_23e2: push si
L_23e3: push word [reset_configured_wide]
L_23e7: call terminal_reset_geometry
L_23ea: add sp,0x4
L_23ed: cmp word [terminal_tab_wrap],0x0
L_23f2: jz short L_2433
L_23f4: or_load si,si
L_23f6: jnz short L_2433
L_23f8: cmp [reset_wide_mode],si
L_23fc: jnz short L_242a
L_23fe: cmp word [bp-0x2],0x4f
L_2402: jna short L_2409
L_2404: mov word [bp-0x2],0x4f
L_2409: mov ax,[screen_attribute_row_bytes]
L_240c: cmp [program_state_7a72],ax
L_2410: jna short L_242a
L_2412: sub_load ax,ax
L_2414: push ax
L_2415: mov al,[screen_attribute_row_bytes]
L_2418: sub_load ah,ah
L_241a: push ax
L_241b: mov al,[screen_viewport_right]
L_241e: mov ah,[reset_data_7a80]
L_2422: push ax
L_2423: push word [attributes_normal_value]
L_2427: call terminal_reset_bios_rectangle
L_242a: mov ax,[bp-0x4]
L_242d: mov dx,[bp-0x2]
L_2430: call screen_set_cursor
L_2433: cmp word [screen_cursor_wrap],0x0
L_2438: jz short L_2440
L_243a: mov ax,0x2
L_243d: jmp short L_2443
L_243f: nop
L_2440: mov ax,0x1
L_2443: push ax
L_2444: call csi_clear_tabs
L_2447: add sp,0x2
L_244a: cmp word [reset_underline_enabled],0x0
L_244f: jz short L_2456
L_2451: call terminal_reset_underline_configured
L_2454: jmp short L_2459
L_2456: call terminal_reset_underline_default
L_2459: cmp word [reset_status_hidden],0x0
L_245e: jnz short L_2463
L_2460: call terminal_reset_status_fill
L_2463: call terminal_reset_status_refresh
L_2466: pop si
L_2467: pop di
L_2468: mov_load sp,bp
L_246a: pop bp
L_246b: ret
