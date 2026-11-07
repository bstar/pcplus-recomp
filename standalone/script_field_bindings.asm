; Diagnostic adapter: actual native cursor adopter, controlled admission.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_script_field,_field_admit,screen_set_cursor
extern _field_unexpected
global _field_request
_field_request:
 push bp
 mov bp,sp
 push si
 push di
 push es
 cmp word [_field_flags],0
 je .enabled
 test word [_field_flags],1
 jz .df
 cli
.df:
 test word [_field_flags],2
 jz .loaded
 std
 jmp .loaded
.enabled:
 sti
 cld
.loaded:
 mov si,0x1234
 mov di,0x5678
 mov ax,0x2468
 mov es,ax
 mov ax,[bp+4]
 mov bx,[bp+6]
 mov [_field_saved_sp],sp
 stc
 pushf
 pop word [_field_saved_flags]
 call far terminal_script_field
 pushf
 pop dx
 cmp dx,[_field_saved_flags]
 jne .bad
 cmp si,0x1234
 jne .bad
 cmp di,0x5678
 jne .bad
 mov cx,es
 cmp cx,0x2468
 jne .bad
 mov cx,ds
 mov dx,ss
 cmp cx,dx
 jne .bad
 cmp sp,[_field_saved_sp]
 jne .bad
 jmp .restore
.bad:
 mov word [_field_abi_bad],1
.restore:
 cld
 sti
 pop es
 pop di
 pop si
 pop bp
 ret
global _aspect_render_admit,attribute_screen_set_cursor_far,_field_adopt_request
extern terminal_script_field_adopt,_field_adoptions
_aspect_render_admit: jmp _field_admit
attribute_screen_set_cursor_far:
 inc word [_field_adoptions]
 call screen_set_cursor
 retf
_field_adopt_request:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov dx,[bp+6]
 call far terminal_script_field_adopt
 pop bp
 ret
global screen_viewport_enter
screen_viewport_enter: jmp _field_unexpected
global screen_viewport_leave
screen_viewport_leave: jmp _field_unexpected
global screen_viewport_refresh
screen_viewport_refresh: jmp _field_unexpected
global _field_set_owners,terminal_script_window_active,terminal_script_confirm_active,render_program_owned
_field_set_owners:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [cs:terminal_script_window_active],ax
 mov ax,[bp+6]
 mov [cs:terminal_script_confirm_active],ax
 mov ax,[bp+8]
 mov [cs:render_program_owned],ax
 pop bp
 ret
terminal_script_window_active: dw 0
terminal_script_confirm_active: dw 0
render_program_owned: dw 0
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global _field_flags
_field_flags: dw 0
global _field_saved_sp
_field_saved_sp: dw 0
global _field_saved_flags
_field_saved_flags: dw 0
global _field_abi_bad
_field_abi_bad: dw 0
global screen_columns,_field_screen_columns
screen_columns:
_field_screen_columns: dw 80
global screen_video_row_bytes,_field_screen_video_row_bytes
screen_video_row_bytes:
_field_screen_video_row_bytes: dw 160
global text_video_segment,_field_text_video_segment
text_video_segment:
_field_text_video_segment: dw 47104
global text_cga_status_port,_field_text_cga_status_port
text_cga_status_port:
_field_text_cga_status_port: dw 0
global text_bios_output,_field_text_bios_output
text_bios_output:
_field_text_bios_output: dw 0
global screen_viewport_offset,_field_screen_viewport_offset
screen_viewport_offset:
_field_screen_viewport_offset: dw 0
global screen_cursor_row,_field_screen_cursor_row
screen_cursor_row:
_field_screen_cursor_row: dw 0
global screen_visible_column,_field_screen_visible_column
screen_visible_column:
_field_screen_visible_column: dw 0
global attributes_current,_field_attributes_current
attributes_current:
_field_attributes_current: dw 7
global screen_viewport_enabled,_field_screen_viewport_enabled
screen_viewport_enabled:
_field_screen_viewport_enabled: dw 0
global screen_viewport_left,_field_screen_viewport_left
screen_viewport_left:
_field_screen_viewport_left: dw 0
global screen_viewport_active,_field_screen_viewport_active
screen_viewport_active:
_field_screen_viewport_active: dw 0
global screen_viewport_right,_field_screen_viewport_right
screen_viewport_right:
_field_screen_viewport_right: dw 79
global screen_video_offset,_field_screen_video_offset
screen_video_offset:
_field_screen_video_offset: dw 0
global screen_previous_column,_field_screen_previous_column
screen_previous_column:
_field_screen_previous_column: dw 0
global screen_attribute_offset,_field_screen_attribute_offset
screen_attribute_offset:
_field_screen_attribute_offset: dw 0
global screen_cursor_column,_field_screen_cursor_column
screen_cursor_column:
_field_screen_cursor_column: dw 0
global screen_previous_row,_field_screen_previous_row
screen_previous_row:
_field_screen_previous_row: dw 0
global screen_attribute_row_bytes,_field_screen_attribute_row_bytes
screen_attribute_row_bytes:
_field_screen_attribute_row_bytes: dw 80
global screen_use_bios_cursor,_field_screen_use_bios_cursor
screen_use_bios_cursor:
_field_screen_use_bios_cursor: dw 1
global csi_last_row,_field_csi_last_row
csi_last_row:
_field_csi_last_row: dw 24
