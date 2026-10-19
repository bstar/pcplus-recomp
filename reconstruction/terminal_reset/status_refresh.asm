; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
%ifdef STATUS_CONFIG_CODE
SEGMENT CONFIG_CODE public class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global terminal_reset_status_refresh
extern text_fill_cells
extern terminal_reset_status_message
extern text_write_packed
extern terminal_reset_ui_75e8
extern terminal_reset_ui_7630
extern terminal_reset_sprintf
extern terminal_reset_uart_status
extern screen_viewport_enabled
extern screen_viewport_active
extern screen_attribute_row_bytes
extern program_state_7a72
extern csi_terminal_id
extern terminal_sink_3988_enabled
extern terminal_sink_398a_enabled
extern terminal_sink_398c_disabled
extern terminal_tab_wrap
extern ui_flow_region_cells
extern ui_flow_video_base
extern ui_flow_coordinate_base
extern reset_status_hidden
extern ui_flow_attribute
extern meta_local_echo
extern meta_script_active
extern keyboard_state_373c
extern reset_scratch
extern reset_data_399a
extern reset_data_3732
extern reset_data_cc9e
extern reset_data_1f6c
extern reset_data_332c
extern reset_data_42b6
extern reset_data_42b4
extern reset_data_42b2
extern reset_data_299c
extern reset_data_1b8a
extern reset_data_1b8c
extern reset_data_1b88
extern reset_data_46ce
extern reset_data_1b86
extern reset_data_29de
extern reset_data_46d0
extern reset_data_7a7c
extern reset_data_cc89
extern reset_data_cc80
extern reset_data_cc77
extern reset_data_cc6e
extern reset_data_cc65
extern reset_data_cc5c
extern reset_data_cc53
extern reset_data_46d2
extern reset_data_432e
extern reset_data_4336
extern reset_data_433e
extern reset_data_4324
extern reset_data_4346
extern reset_data_4350
extern reset_data_46c1
extern reset_data_46c4
extern terminal_reset_script_label
%define short
%else
ORG 0x2fb8
%define text_fill_cells 0x6c20
%define terminal_reset_status_message 0x3226
%define text_write_packed 0x6cb4
%define terminal_reset_ui_75e8 0x75e8
%define terminal_reset_ui_7630 0x7630
%define terminal_reset_sprintf 0x82b6
%define terminal_reset_uart_status 0xaa5c
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_active 0x3256
%define screen_attribute_row_bytes 0x325a
%define program_state_7a72 0x7a72
%define csi_terminal_id 0x1d18
%define terminal_sink_3988_enabled 0x3988
%define terminal_sink_398a_enabled 0x398a
%define terminal_sink_398c_disabled 0x398c
%define terminal_tab_wrap 0x903e
%define ui_flow_region_cells 0x3250
%define ui_flow_video_base 0x7a82
%define ui_flow_coordinate_base 0x7a84
%define reset_status_hidden 0x1d46
%define ui_flow_attribute 0x1f6e
%define meta_local_echo 0x1d1a
%define meta_script_active 0x4b02
%define keyboard_state_373c 0x373c
%define reset_scratch 0xcc4a
%define reset_data_399a 0x399a
%define reset_data_3732 0x3732
%define reset_data_cc9e 0xcc9e
%define reset_data_1f6c 0x1f6c
%define reset_data_332c 0x332c
%define reset_data_42b6 0x42b6
%define reset_data_42b4 0x42b4
%define reset_data_42b2 0x42b2
%define reset_data_299c 0x299c
%define reset_data_1b8a 0x1b8a
%define reset_data_1b8c 0x1b8c
%define reset_data_1b88 0x1b88
%define reset_data_46ce 0x46ce
%define reset_data_1b86 0x1b86
%define reset_data_29de 0x29de
%define reset_data_46d0 0x46d0
%define reset_data_7a7c 0x7a7c
%define reset_data_cc89 0xcc89
%define reset_data_cc80 0xcc80
%define reset_data_cc77 0xcc77
%define reset_data_cc6e 0xcc6e
%define reset_data_cc65 0xcc65
%define reset_data_cc5c 0xcc5c
%define reset_data_cc53 0xcc53
%define reset_data_46d2 0x46d2
%define reset_data_432e 0x432e
%define reset_data_4336 0x4336
%define reset_data_433e 0x433e
%define reset_data_4324 0x4324
%define reset_data_4346 0x4346
%define reset_data_4350 0x4350
%define reset_data_46c1 0x46c1
%define reset_data_46c4 0x46c4
%define terminal_reset_script_label 0xd464
%endif
%include "encodings.inc"
terminal_reset_status_refresh:
L_2fb8: push bp
L_2fb9: mov_load bp,sp
L_2fbb: sub sp,0x5c
L_2fbe: push di
L_2fbf: push si
L_2fc0: mov ax,[ui_flow_region_cells]
L_2fc3: sub ax,strict word 0x50
L_2fc6: mov_load cx,ax
L_2fc8: sar ax,1
L_2fca: mov [bp-0x8],ax
L_2fcd: add ax,[ui_flow_coordinate_base]
L_2fd1: mov [bp-0xa],ax
L_2fd4: add cx,[ui_flow_video_base]
L_2fd8: mov [bp-0x6],cx
L_2fdb: cmp word [reset_status_hidden],0x0
L_2fe0: jz short L_2fe5
L_2fe2: jmp near L_31b5
L_2fe5: cmp word [terminal_tab_wrap],0x0
L_2fea: jz short L_302c
L_2fec: cmp word [reset_data_3732],0x0
L_2ff1: jz short L_302c
L_2ff3: mov ax,reset_data_cc89
L_2ff6: push ax
L_2ff7: mov ax,reset_data_cc80
L_2ffa: push ax
L_2ffb: mov ax,reset_data_cc77
L_2ffe: push ax
L_2fff: mov ax,reset_data_cc6e
L_3002: push ax
L_3003: mov ax,reset_data_cc65
L_3006: push ax
L_3007: mov ax,reset_data_cc5c
L_300a: push ax
L_300b: mov ax,reset_data_cc53
L_300e: push ax
L_300f: mov ax,reset_scratch
L_3012: push ax
L_3013: mov ax,reset_data_46d2
L_3016: push ax
L_3017: lea ax,[bp-0x5c]
L_301a: push ax
L_301b: call terminal_reset_sprintf
L_301e: add sp,0x14
L_3021: lea ax,[bp-0x5c]
L_3024: push ax
L_3025: call terminal_reset_status_message
L_3028: pop bx
L_3029: jmp near L_31b5
L_302c: cmp word [reset_data_399a],0x0
L_3031: jz short L_3038
L_3033: mov ax,reset_data_cc9e
L_3036: jmp short L_3024
L_3038: cmp word [meta_script_active],0x0
L_303d: jz short L_304b
L_303f: mov word [bp-0x4],0x1
L_3044: mov word [bp-0x2],terminal_reset_script_label
L_3049: jmp short L_307a
L_304b: cmp word [keyboard_state_373c],0x0
L_3050: jnz short L_3063
L_3052: cmp word [reset_data_332c],0x0
L_3057: jnz short L_3063
L_3059: mov word [bp-0x4],0x0
L_305e: mov ax,[reset_data_42b6]
L_3061: jmp short L_3077
L_3063: mov word [bp-0x4],0x1
L_3068: cmp word [keyboard_state_373c],0x0
L_306d: jz short L_3074
L_306f: mov ax,[reset_data_42b4]
L_3072: jmp short L_3077
L_3074: mov ax,[reset_data_42b2]
L_3077: mov [bp-0x2],ax
L_307a: cmp word [terminal_sink_398a_enabled],0x0
L_307f: jz short L_308d
L_3081: cmp word [terminal_sink_398c_disabled],0x0
L_3086: jnz short L_308d
L_3088: mov si,reset_data_432e
L_308b: jmp short L_309c
L_308d: cmp word [terminal_sink_398a_enabled],0x0
L_3092: jz short L_3099
L_3094: mov si,reset_data_4336
L_3097: jmp short L_309c
L_3099: mov si,reset_data_433e
L_309c: cmp word [reset_data_332c],0x0
L_30a1: jz short L_30a8
L_30a3: mov di,reset_data_4324
L_30a6: jmp short L_30b2
L_30a8: mov bx,[csi_terminal_id]
L_30ac: shl bx,1
L_30ae: mov di,[bx+reset_data_299c]
L_30b2: call terminal_reset_uart_status
L_30b5: or_load ax,ax
L_30b7: jz short L_30be
L_30b9: mov ax,reset_data_4346
L_30bc: jmp short L_30c1
L_30be: mov ax,reset_data_4350
L_30c1: push ax
L_30c2: cmp word [terminal_sink_3988_enabled],0x0
L_30c7: jz short L_30ce
L_30c9: mov ax,reset_data_46c1
L_30cc: jmp short L_30d1
L_30ce: mov ax,reset_data_46c4
L_30d1: push ax
L_30d2: push si
L_30d3: push word [reset_data_1b8a]
L_30d7: push word [reset_data_1b8c]
L_30db: mov bx,[reset_data_1b88]
L_30df: add bx,[reset_data_46ce]
L_30e3: mov al,[bx]
L_30e5: cbw
L_30e6: push ax
L_30e7: mov bx,[reset_data_1b86]
L_30eb: shl bx,1
L_30ed: push word [bx+reset_data_29de]
L_30f1: cmp word [meta_local_echo],0x1
L_30f6: sbb_load ax,ax
L_30f8: and al,0xfe
L_30fa: add ax,strict word 0x48
L_30fd: push ax
L_30fe: push di
L_30ff: push word [bp-0x2]
L_3102: push word [reset_data_46d0]
L_3106: push word [reset_data_1f6c]
L_310a: push word [bp-0xa]
L_310d: call terminal_reset_ui_75e8
L_3110: add sp,0x1a
L_3113: cmp word [program_state_7a72],0x50
L_3118: jng short L_3174
L_311a: mov al,[reset_data_1f6c]
L_311d: sub_load ah,ah
L_311f: mov_load cx,ax
L_3121: mov ah,0xb0
L_3123: mov_load si,ax
L_3125: mov_load di,cx
L_3127: or di,0xb300
L_312b: push ax
L_312c: push word [ui_flow_video_base]
L_3130: push word [bp-0x8]
L_3133: call text_fill_cells
L_3136: push si
L_3137: mov ax,[bp-0x6]
L_313a: add ax,0xa0
L_313d: mov [bp-0x2],ax
L_3140: push ax
L_3141: push word [bp-0x8]
L_3144: call text_fill_cells
L_3147: mov ax,[program_state_7a72]
L_314a: cmp [screen_attribute_row_bytes],ax
L_314e: jnc short L_315c
L_3150: push si
L_3151: push word [bp-0x2]
L_3154: sub ax,[screen_attribute_row_bytes]
L_3158: push ax
L_3159: call text_fill_cells
L_315c: cmp word [screen_attribute_row_bytes],0x50
L_3161: jna short L_316d
L_3163: push di
L_3164: mov ax,[bp-0x6]
L_3167: dec ax
L_3168: dec ax
L_3169: push ax
L_316a: call text_write_packed
L_316d: push di
L_316e: push word [bp-0x2]
L_3171: call text_write_packed
L_3174: cmp word [screen_viewport_enabled],0x0
L_3179: jz short L_319d
L_317b: cmp word [screen_viewport_active],0x0
L_3180: jz short L_3190
L_3182: mov al,[ui_flow_attribute]
L_3185: mov ah,0x1a
L_3187: push ax
L_3188: mov ax,[reset_data_7a7c]
L_318b: dec ax
L_318c: dec ax
L_318d: push ax
L_318e: jmp short L_319a
L_3190: mov al,[ui_flow_attribute]
L_3193: mov ah,0x1b
L_3195: push ax
L_3196: push word [ui_flow_video_base]
L_319a: call text_write_packed
L_319d: cmp word [bp-0x4],0x0
L_31a1: jz short L_31b5
L_31a3: mov al,[ui_flow_attribute]
L_31a6: push ax
L_31a7: mov ax,[bp-0x6]
L_31aa: add ax,strict word 0x3
L_31ad: push ax
L_31ae: mov ax,0xe
L_31b1: push ax
L_31b2: call terminal_reset_ui_7630
L_31b5: pop si
L_31b6: pop di
L_31b7: mov_load sp,bp
L_31b9: pop bp
L_31ba: ret
