; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_geometry
extern terminal_reset_clear_shadow
extern terminal_reset_width
extern screen_set_cursor
extern erase_move_bytes
extern terminal_reset_free_far
extern terminal_reset_allocate_far
extern terminal_reset_application_error
extern erase_repair_attributes
extern screen_viewport_enabled
extern screen_viewport_left
extern screen_previous_column
extern screen_attribute_offset
extern screen_attribute_row_bytes
extern screen_attributes_base
extern screen_cursor_wrap
extern program_state_7a72
extern erase_attribute_values_base
extern erase_shadow_offset
extern erase_shadow_segment
extern ui_flow_region_cells
extern program_state_7a74
extern reset_shadow_bytes
extern reset_wide_mode
extern reset_geometry_initialized
extern reset_configured_wide
extern reset_data_ceae
extern reset_data_2c54
%define short
%else
ORG 0x281c
%define terminal_reset_clear_shadow 0x27ea
%define terminal_reset_width 0x2a36
%define screen_set_cursor 0x1bbe
%define erase_move_bytes 0x85b4
%define terminal_reset_free_far 0x85fc
%define terminal_reset_allocate_far 0x860f
%define terminal_reset_application_error 0x427f
%define erase_repair_attributes 0x2d98
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_left 0xce2e
%define screen_previous_column 0x3348
%define screen_attribute_offset 0x3346
%define screen_attribute_row_bytes 0x325a
%define screen_attributes_base 0x39c4
%define screen_cursor_wrap 0x900c
%define program_state_7a72 0x7a72
%define erase_attribute_values_base 0x39c2
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%define ui_flow_region_cells 0x3250
%define program_state_7a74 0x7a74
%define reset_shadow_bytes 0xce02
%define reset_wide_mode 0x3254
%define reset_geometry_initialized 0x469a
%define reset_configured_wide 0x1d2e
%define reset_data_ceae 0xceae
%define reset_data_2c54 0x2c54
%endif
%include "encodings.inc"
terminal_reset_geometry:
L_281c: push bp
L_281d: mov_load bp,sp
L_281f: sub sp,0x6
L_2822: push di
L_2823: push si
L_2824: sub_load di,di
L_2826: cmp [reset_geometry_initialized],di
L_282a: jz short L_283c
L_282c: sub_load ax,ax
L_282e: cwd
L_282f: call screen_set_cursor
L_2832: sub_load ax,ax
L_2834: mov [screen_previous_column],ax
L_2837: mov [screen_attribute_offset],ax
L_283a: jmp short L_2842
L_283c: mov word [reset_geometry_initialized],0x1
L_2842: mov ax,[bp+0x4]
L_2845: cmp [reset_wide_mode],ax
L_2849: jnz short L_284e
L_284b: jmp near L_2962
L_284e: cmp_load ax,di
L_2850: jnz short L_2855
L_2852: jmp near L_2902
L_2855: mov ax,0x1
L_2858: push ax
L_2859: call terminal_reset_width
L_285c: add sp,0x2
L_285f: cmp [screen_cursor_wrap],di
L_2863: jnz short L_2868
L_2865: jmp near L_295c
L_2868: cmp [bp+0x6],di
L_286b: jz short L_2870
L_286d: jmp near L_295c
L_2870: mov di,0xbdc
L_2873: mov word [bp-0x4],0x730
L_2878: mov word [bp-0x6],0x17
L_287d: mov_load si,di
L_287f: mov ax,0x50
L_2882: push ax
L_2883: mov cx,[screen_attributes_base]
L_2887: add cx,[bp-0x4]
L_288a: push cx
L_288b: mov cx,[screen_attributes_base]
L_288f: add_load cx,si
L_2891: push cx
L_2892: call erase_move_bytes
L_2895: add sp,0x6
L_2898: sub_load ax,ax
L_289a: mov bx,[screen_attributes_base]
L_289e: mov cx,0x34
L_28a1: lea di,[bx+si+0x50]
L_28a4: push ds
L_28a5: pop es
L_28a6: rep stosb
L_28a8: mov ax,0x50
L_28ab: push ax
L_28ac: mov cx,[erase_attribute_values_base]
L_28b0: add cx,[bp-0x4]
L_28b3: push cx
L_28b4: mov cx,[erase_attribute_values_base]
L_28b8: add_load cx,si
L_28ba: push cx
L_28bb: call erase_move_bytes
L_28be: add sp,0x6
L_28c1: sub_load ax,ax
L_28c3: mov bx,[erase_attribute_values_base]
L_28c7: mov cx,0x34
L_28ca: lea di,[bx+si+0x50]
L_28cd: push ds
L_28ce: pop es
L_28cf: rep stosb
L_28d1: sub si,0x84
L_28d5: sub word [bp-0x4],0x50
L_28d9: dec word [bp-0x6]
L_28dc: jnz short L_287f
L_28de: sub_load ax,ax
L_28e0: mov bx,[screen_attributes_base]
L_28e4: mov cx,0x34
L_28e7: lea di,[bx+0x50]
L_28ea: rep stosb
L_28ec: sub_load ax,ax
L_28ee: mov bx,[erase_attribute_values_base]
L_28f2: mov cx,0x34
L_28f5: lea di,[bx+0x50]
L_28f8: rep stosb
L_28fa: mov si,0x1
L_28fd: mov_load di,si
L_28ff: jmp short L_295c
L_2901: nop
L_2902: sub_load ax,ax
L_2904: push ax
L_2905: call terminal_reset_width
L_2908: add sp,0x2
L_290b: cmp [screen_cursor_wrap],di
L_290f: jz short L_295c
L_2911: cmp [bp+0x6],di
L_2914: jnz short L_295c
L_2916: mov di,0x50
L_2919: mov si,0x84
L_291c: mov ax,0x50
L_291f: push ax
L_2920: mov cx,[screen_attributes_base]
L_2924: add_load cx,si
L_2926: push cx
L_2927: mov cx,[screen_attributes_base]
L_292b: add_load cx,di
L_292d: push cx
L_292e: call erase_move_bytes
L_2931: add sp,0x6
L_2934: mov ax,0x50
L_2937: push ax
L_2938: mov cx,[erase_attribute_values_base]
L_293c: add_load cx,si
L_293e: push cx
L_293f: mov cx,[erase_attribute_values_base]
L_2943: add_load cx,di
L_2945: push cx
L_2946: call erase_move_bytes
L_2949: add sp,0x6
L_294c: add di,0x50
L_294f: add si,0x84
L_2953: cmp si,0xbdc
L_2957: jna short L_291c
L_2959: mov di,0x1
L_295c: mov ax,[bp+0x4]
L_295f: mov [reset_wide_mode],ax
L_2962: mov ax,[screen_attribute_row_bytes]
L_2965: cmp [program_state_7a72],ax
L_2969: jnc short L_297c
L_296b: mov word [screen_viewport_enabled],0x1
L_2971: mov ax,[program_state_7a72]
L_2974: mov [ui_flow_region_cells],ax
L_2977: mov ax,[screen_attribute_row_bytes]
L_297a: jmp short L_2988
L_297c: mov word [screen_viewport_enabled],0x0
L_2982: mov [ui_flow_region_cells],ax
L_2985: mov ax,[program_state_7a72]
L_2988: mov [reset_data_ceae],ax
L_298b: cmp word [screen_viewport_enabled],0x0
L_2990: jz short L_2a00
L_2992: mov ax,[screen_attribute_row_bytes]
L_2995: mul word [program_state_7a74]
L_2999: mov_load si,ax
L_299b: shl si,1
L_299d: mov ax,[erase_shadow_segment]
L_29a0: or ax,[erase_shadow_offset]
L_29a4: jz short L_29ba
L_29a6: cmp [reset_shadow_bytes],si
L_29aa: jz short L_29cc
L_29ac: push word [erase_shadow_segment]
L_29b0: push word [erase_shadow_offset]
L_29b4: call terminal_reset_free_far
L_29b7: add sp,0x4
L_29ba: push si
L_29bb: call terminal_reset_allocate_far
L_29be: add sp,0x2
L_29c1: mov [erase_shadow_offset],ax
L_29c4: mov [erase_shadow_segment],dx
L_29c8: mov [reset_shadow_bytes],si
L_29cc: mov ax,[erase_shadow_segment]
L_29cf: or ax,[erase_shadow_offset]
L_29d3: jz short L_29da
L_29d5: call terminal_reset_clear_shadow
L_29d8: jmp short L_29f3
L_29da: lea bx,[reset_data_2c54]
L_29de: call terminal_reset_application_error
L_29e1: mov word [screen_viewport_enabled],0x0
L_29e7: sub_load ax,ax
L_29e9: mov [reset_configured_wide],ax
L_29ec: push ax
L_29ed: call terminal_reset_width
L_29f0: add sp,0x2
L_29f3: mov ax,[screen_attribute_row_bytes]
L_29f6: sub ax,[program_state_7a72]
L_29fa: mov [screen_viewport_left],ax
L_29fd: jmp short L_2a25
L_29ff: nop
L_2a00: mov word [screen_viewport_left],0x0
L_2a06: mov ax,[erase_shadow_segment]
L_2a09: or ax,[erase_shadow_offset]
L_2a0d: jz short L_2a1d
L_2a0f: push word [erase_shadow_segment]
L_2a13: push word [erase_shadow_offset]
L_2a17: call terminal_reset_free_far
L_2a1a: add sp,0x4
L_2a1d: sub_load ax,ax
L_2a1f: mov [erase_shadow_segment],ax
L_2a22: mov [erase_shadow_offset],ax
L_2a25: or_load di,di
L_2a27: jz short L_2a2f
L_2a29: sub_load ax,ax
L_2a2b: push ax
L_2a2c: call erase_repair_attributes
L_2a2f: pop si
L_2a30: pop di
L_2a31: mov_load sp,bp
L_2a33: pop bp
L_2a34: ret
