; Original DS and service locations versus OMF linker symbols.
%ifdef ANSI_OMF
extern ansi_command
extern ansi_control_character
extern ansi_next_byte
extern ansi_parameter_count
extern ansi_parameters
extern ansi_private
extern ansi_secondary
extern ansi_unread_byte
extern attributes_blink
extern attributes_blink_active
extern attributes_bold
extern attributes_bold_active
extern attributes_current
extern attributes_default_transform
extern attributes_monochrome
extern attributes_normal
extern attributes_normal_value
extern attributes_reverse
extern attributes_reverse_active
extern attributes_underline
extern csi_clear_tabs
extern csi_column_count
extern csi_device_status
extern csi_erase_attribute
extern csi_last_column
extern csi_last_row
extern csi_media_copy
extern csi_origin_bottom
extern csi_origin_mode
extern csi_origin_row
extern csi_previous_terminal_id
extern csi_primary_attributes
extern csi_reset_modes
extern csi_reset_scroll_region
extern csi_reset_terminal
extern csi_restore_cursor
extern csi_row_count
extern csi_save_cursor
extern csi_scroll_bottom
extern csi_scroll_top
extern csi_secondary_322c
extern csi_secondary_7529
extern csi_secondary_prefix
extern csi_service_12c8
extern csi_service_2530
extern csi_service_d270
extern csi_service_d440
extern csi_service_d668
extern csi_service_d73c
extern csi_service_d844
extern csi_service_d85e
extern csi_service_d8b6
extern csi_service_da12
extern csi_service_da84
extern csi_service_daf2
extern csi_set_modes
extern csi_terminal_id
extern csi_transmit_byte
extern csi_transmit_string
extern csi_wrap_pending
extern screen_cursor_column
extern screen_cursor_down
extern screen_cursor_left
extern screen_cursor_right
extern screen_cursor_row
extern screen_cursor_up
extern screen_set_cursor
%else
%define ansi_control_character 0x610
%define csi_service_12c8 0x12c8
%define screen_set_cursor 0x1bbe
%define attributes_normal 0x1c8c
%define attributes_bold 0x1cb2
%define attributes_underline 0x1cce
%define attributes_blink 0x1ce4
%define attributes_reverse 0x1cf0
%define csi_terminal_id 0x1d18
%define attributes_normal_value 0x1d32
%define attributes_default_transform 0x1d6c
%define screen_cursor_down 0x1e0c
%define screen_cursor_left 0x1e30
%define screen_cursor_right 0x1ea0
%define screen_cursor_up 0x1efc
%define attributes_current 0x1f70
%define csi_reset_terminal 0x20a4
%define csi_clear_tabs 0x246c
%define csi_reset_scroll_region 0x250a
%define csi_service_2530 0x2530
%define attributes_reverse_active 0x321c
%define csi_previous_terminal_id 0x321e
%define csi_secondary_322c 0x322c
%define csi_last_column 0x3258
%define csi_column_count 0x325a
%define csi_wrap_pending 0x3342
%define csi_last_row 0x334a
%define csi_row_count 0x334c
%define attributes_bold_active 0x397c
%define attributes_blink_active 0x397e
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define ansi_next_byte 0x5ca0
%define csi_secondary_prefix 0x7525
%define csi_secondary_7529 0x7529
%define attributes_monochrome 0x8ff6
%define csi_transmit_byte 0xab0b
%define csi_transmit_string 0xabac
%define ansi_unread_byte 0xabde
%define ansi_parameters 0xcb3c
%define ansi_parameter_count 0xcb5c
%define ansi_command 0xcd38
%define csi_origin_mode 0xcdd2
%define csi_scroll_top 0xce0e
%define csi_scroll_bottom 0xce3a
%define ansi_private 0xceac
%define csi_origin_row 0xceb0
%define ansi_secondary 0xcee2
%define csi_origin_bottom 0xcee4
%define csi_erase_attribute 0xd008
%define csi_service_d270 0xd270
%define csi_service_d440 0xd440
%define csi_service_d668 0xd668
%define csi_service_d73c 0xd73c
%define csi_service_d844 0xd844
%define csi_service_d85e 0xd85e
%define csi_service_d8b6 0xd8b6
%define csi_service_da12 0xda12
%define csi_service_da84 0xda84
%define csi_service_daf2 0xdaf2
%define csi_primary_attributes 0xdd58
%define csi_save_cursor 0xdd74
%define csi_restore_cursor 0xddbc
%define csi_device_status 0xde04
%define csi_set_modes 0xde98
%define csi_reset_modes 0xdf7e
%define csi_media_copy 0xe084
%endif
