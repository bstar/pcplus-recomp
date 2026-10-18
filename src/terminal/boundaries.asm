; Link real recovered services; missing features unwind through live cleanup.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_abort,csi_unimplemented_service,terminal_keyboard_mode
global ansi_escape_service_12c8,csi_service_12c8
extern screen_wrap_forward,screen_linefeed,scroll_up,scroll_index,scroll_reverse_index
ansi_escape_service_12c8:
csi_service_12c8:
 jmp screen_wrap_forward
extern csi_clear_tabs
extern csi_reset_scroll_region
global screen_adjust_attribute_boundary
screen_adjust_attribute_boundary:
 mov ax,0x2adc
 jmp csi_unimplemented
global screen_viewport_refresh
screen_viewport_refresh:
 mov ax,0x2fb8
 jmp csi_unimplemented
global screen_viewport_enter
screen_viewport_enter:
 mov ax,0x482a
 jmp csi_unimplemented
global screen_viewport_leave
screen_viewport_leave:
 mov ax,0x4850
 jmp csi_unimplemented
global ansi_escape_service_da46
ansi_escape_service_da46:
 jmp scroll_index
global ansi_escape_service_da84
global csi_service_da84
ansi_escape_service_da84:
csi_service_da84:
 jmp scroll_reverse_index
global ansi_escape_service_dd58
extern csi_primary_attributes,csi_device_status
ansi_escape_service_dd58:
 jmp csi_primary_attributes
global ansi_escape_service_dd74,ansi_escape_service_ddbc
extern csi_save_cursor,csi_restore_cursor
; Tail jumps preserve the caller-cleanup mode argument beneath the return address.
ansi_escape_service_dd74:
 jmp csi_save_cursor
ansi_escape_service_ddbc:
 jmp csi_restore_cursor
extern csi_set_modes,csi_reset_modes
global modes_keyboard_map
modes_keyboard_map:
 jmp terminal_keyboard_mode
global modes_screen_width
modes_screen_width:
 mov ax,0x2a6e
 jmp csi_unimplemented
global csi_media_copy
csi_media_copy:
 mov ax,0xe084
 jmp csi_unimplemented
global ansi_escape_service_e0f8
ansi_escape_service_e0f8:
 mov ax,0xe0f8
 jmp csi_unimplemented
global ansi_escape_service_ec94
ansi_escape_service_ec94:
 mov ax,0xec94
 jmp csi_unimplemented
global erase_complex_protected,erase_repair_attributes
erase_complex_protected:
 mov ax,0xd05f
 jmp csi_unimplemented
erase_repair_attributes:
 mov ax,0x2d98
 jmp csi_unimplemented
csi_unimplemented:
 mov [csi_unimplemented_service],ax
 jmp terminal_abort
global render_service_b9f7
render_service_b9f7:
 mov ax,0xb9f7
 jmp csi_unimplemented
global render_font_output
render_font_output:
 mov ax,0xbb53
 jmp csi_unimplemented
global terminal_sink_36fc
terminal_sink_36fc:
 mov ax,0x36fc
 jmp csi_unimplemented
global terminal_sink_8436
terminal_sink_8436:
 mov ax,0x8436
 jmp csi_unimplemented
global terminal_sink_427f
terminal_sink_427f:
 mov ax,0x427f
 jmp csi_unimplemented
global terminal_sink_bb23
terminal_sink_bb23:
 mov ax,0xbb23
 jmp csi_unimplemented
global terminal_escape_b98b
terminal_escape_b98b:
 mov ax,0xb98b
 jmp csi_unimplemented
global terminal_escape_b9a3
terminal_escape_b9a3:
 mov ax,0xb9a3
 jmp csi_unimplemented
global terminal_escape_b97f
terminal_escape_b97f:
 mov ax,0xb97f
 jmp csi_unimplemented
global terminal_escape_b9af
terminal_escape_b9af:
 mov ax,0xb9af
 jmp csi_unimplemented
global terminal_escape_b997
terminal_escape_b997:
 mov ax,0xb997
 jmp csi_unimplemented
global terminal_escape_bb3b
terminal_escape_bb3b:
 mov ax,0xbb3b
 jmp csi_unimplemented
global terminal_control_0e70
terminal_control_0e70:
 mov ax,0xe70
 jmp csi_unimplemented
global terminal_control_4cd7
terminal_control_4cd7:
 mov ax,0x4cd7
 jmp csi_unimplemented
global terminal_control_0e7c
terminal_control_0e7c:
 mov ax,0xe7c
 jmp csi_unimplemented
global terminal_control_0ede
terminal_control_0ede:
 mov ax,0xede
 jmp csi_unimplemented
global terminal_control_3778
terminal_control_3778:
 push bp
 mov ax,0x0e07
 xor bx,bx
 int 0x10
 pop bp
 ret
global terminal_control_1040
terminal_control_1040:
 mov ax,0x1040
 jmp csi_unimplemented
global terminal_control_1064
terminal_control_1064:
 mov ax,0x1064
 jmp csi_unimplemented
global terminal_control_1096
terminal_control_1096:
 mov ax,0x1096
 jmp csi_unimplemented
global terminal_control_10ce
terminal_control_10ce:
 mov ax,0x10ce
 jmp csi_unimplemented
global terminal_control_10fc
terminal_control_10fc:
 mov ax,0x10fc
 jmp csi_unimplemented
global terminal_control_110a
terminal_control_110a:
 mov ax,0x110a
 jmp csi_unimplemented
global terminal_control_113e
terminal_control_113e:
 mov ax,0x113e
 jmp csi_unimplemented
global terminal_control_115c
terminal_control_115c:
 mov ax,0x115c
 jmp csi_unimplemented
global terminal_control_1190
terminal_control_1190:
 mov ax,0x1190
 jmp csi_unimplemented
global terminal_control_123c
terminal_control_123c:
 mov ax,0x123c
 jmp csi_unimplemented
global terminal_control_1248
terminal_control_1248:
 mov ax,0x1248
 jmp csi_unimplemented
global terminal_control_127e
terminal_control_127e:
 mov ax,0x127e
 jmp csi_unimplemented
global terminal_control_1292
terminal_control_1292:
 mov ax,0x1292
 jmp csi_unimplemented
global terminal_control_12b0
terminal_control_12b0:
 mov ax,0x12b0
 jmp csi_unimplemented
global terminal_control_ba33
terminal_control_ba33:
 mov ax,0xba33
 jmp csi_unimplemented
global terminal_control_b9eb
terminal_control_b9eb:
 mov ax,0xb9eb
 jmp csi_unimplemented
global terminal_control_6dca
terminal_control_6dca:
 mov ax,0x6dca
 jmp csi_unimplemented
global terminal_control_aad9
terminal_control_aad9:
 mov ax,0xaad9
 jmp csi_unimplemented
global terminal_control_0dae
terminal_control_0dae:
 mov ax,0xdae
 jmp csi_unimplemented
global terminal_control_bb83
terminal_control_bb83:
 mov ax,0xbb83
 jmp csi_unimplemented
