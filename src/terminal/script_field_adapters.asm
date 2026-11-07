; Parent integration adapters; no RPC publication here. Admission C lives in
; ASPECT_CODE, and the checked caller supplies a bounded physical cursor plus
; retained viewport origin to the native cursor adopter.
%ifdef ASPECT_GET_DISPLAY
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern _aspect_render_admit,attribute_screen_set_cursor_far
extern screen_attribute_row_bytes,csi_last_row
extern terminal_script_window_active,terminal_script_confirm_active,render_program_owned
extern script_break_ui_active
global terminal_script_field_admit,terminal_script_field_adopt
terminal_script_field_admit:
 mov ax,[cs:terminal_script_window_active]
 or ax,[cs:terminal_script_confirm_active]
 or ax,[cs:render_program_owned]
 or ax,[script_break_ui_active]
 jnz .state
 call _aspect_render_admit
 retf
.state:
 mov ax,10
 retf
terminal_script_field_adopt:
 cmp ax,[csi_last_row]
 ja .operand
 cmp dx,[screen_attribute_row_bytes]
 jae .operand
 call far attribute_screen_set_cursor_far
 xor ax,ax
 retf
.operand:
 mov ax,7
 retf
%endif
