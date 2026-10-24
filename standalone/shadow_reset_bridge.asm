; Bind the checked source-owned DOS allocator to the actual native geometry.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_reset_test_initialize,terminal_reset_width,modes_width_request_native
extern reset_data_image,erase_shadow_offset,erase_shadow_segment,reset_shadow_bytes
extern program_state_7a72,program_state_7a74,text_cga_status_port,screen_use_bios_cursor
extern reset_configured_wide,reset_status_hidden,terminal_dec_keys
extern screen_attributes_base,erase_attribute_values_base,screen_attribute_cells,erase_attribute_values
extern csi_last_row,screen_last_row,screen_bottom_margin,screen_viewport_right
global _shadow_native_initialize,_shadow_native_invoke,_shadow_entry_flags,_shadow_boot_write
global _shadow_request_if_off,_shadow_request_df
extern _shadow_request
_shadow_request_if_off:
 pushf
 cli
 mov ax,1
 push ax
 call _shadow_request
 add sp,2
 popf
 ret
_shadow_request_df:
 pushf
 std
 mov ax,1
 push ax
 call _shadow_request
 add sp,2
 popf
 ret
_shadow_boot_write:
 mov [boot_info],ds
 mov [boot_info+2],ss
 mov [boot_info+4],sp
 pushf
 pop word [boot_info+6]
 pushf
 push ax
 push bx
 push cx
 push dx
 mov dx,boot_name
 xor cx,cx
 mov ax,0x3c00
 int 0x21
 jc .done
 mov bx,ax
 mov dx,boot_info
 mov cx,8
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.done:
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
_shadow_entry_flags:
 pushf
 pop ax
 ret
_shadow_native_initialize:
 call terminal_reset_test_initialize
 xor ax,ax
 push ax
 call terminal_reset_width
 add sp,2
 mov word [program_state_7a74],24
 mov word [terminal_dec_keys],1
 mov word [csi_last_row],23
 mov word [screen_last_row],23
 mov word [screen_bottom_margin],23
 mov word [screen_viewport_right],79
 ret
_shadow_native_invoke:
 push bp
 mov bp,sp
 push word [bp+4]
 call modes_width_request_native
 pop bp
 ret
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
boot_name: db 'D:\BOOT.BIN',0
boot_info: times 8 db 0
