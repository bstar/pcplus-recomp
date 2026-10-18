; Symbolic startup function pointers; verified original DS tables.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _DATA public align=16 class=DATA use16
extern ansi_escape_entry
extern screen_wrap_forward
extern terminal_backspace
extern terminal_carriage_return
extern terminal_control_0e62
extern terminal_control_0e70
extern terminal_control_0e7c
extern terminal_control_0ede
extern terminal_control_0f62
extern terminal_control_0fb0
extern terminal_control_1040
extern terminal_control_1064
extern terminal_control_1096
extern terminal_control_10ce
extern terminal_control_10fc
extern terminal_control_110a
extern terminal_control_113e
extern terminal_control_115c
extern terminal_control_1190
extern terminal_control_11a8
extern terminal_control_123c
extern terminal_control_1248
extern terminal_control_127e
extern terminal_control_1292
extern terminal_control_12b0
extern terminal_control_3778
extern terminal_control_4cd7
extern terminal_escape_b97f
extern terminal_escape_b98b
extern terminal_escape_b997
extern terminal_escape_b9a3
extern terminal_escape_b9af
extern terminal_escape_bb3b
extern terminal_ignore_control
extern terminal_linefeed
extern terminal_tab
global terminal_escape_dispatch_table,terminal_control_dispatch_table
%else
ORG 0x445e
%define terminal_ignore_control 0x0e60
%define terminal_escape_b98b 0xb98b
%define ansi_escape_entry 0xb973
%define terminal_escape_b9a3 0xb9a3
%define terminal_escape_b97f 0xb97f
%define terminal_escape_b9af 0xb9af
%define terminal_escape_b997 0xb997
%define terminal_escape_bb3b 0xbb3b
%define terminal_control_0e62 0x0e62
%define terminal_control_0e70 0x0e70
%define terminal_control_4cd7 0x4cd7
%define terminal_control_0e7c 0x0e7c
%define terminal_control_0ede 0x0ede
%define terminal_control_3778 0x3778
%define terminal_backspace 0x0eea
%define terminal_tab 0x0a8c
%define terminal_linefeed 0x0f3e
%define terminal_control_0f62 0x0f62
%define terminal_control_0fb0 0x0fb0
%define terminal_carriage_return 0x1002
%define terminal_control_1040 0x1040
%define terminal_control_1064 0x1064
%define terminal_control_1096 0x1096
%define terminal_control_10ce 0x10ce
%define terminal_control_10fc 0x10fc
%define terminal_control_110a 0x110a
%define terminal_control_113e 0x113e
%define terminal_control_115c 0x115c
%define terminal_control_1190 0x1190
%define terminal_control_11a8 0x11a8
%define terminal_control_123c 0x123c
%define terminal_control_1248 0x1248
%define terminal_control_127e 0x127e
%define terminal_control_1292 0x1292
%define terminal_control_12b0 0x12b0
%define screen_wrap_forward 0x12c8
%endif
terminal_escape_dispatch_table:
 dw terminal_ignore_control
 dw terminal_escape_b98b
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw ansi_escape_entry
 dw terminal_escape_b9a3
 dw terminal_escape_b97f
 dw terminal_escape_b97f
 dw terminal_ignore_control
 dw terminal_ignore_control
 dw terminal_ignore_control
 dw terminal_escape_b9af
 dw terminal_escape_b9af
 dw terminal_escape_b997
 dw terminal_escape_b997
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
 dw terminal_escape_bb3b
terminal_control_dispatch_table:
 dw terminal_ignore_control
 dw terminal_control_0e62
 dw terminal_control_0e70
 dw terminal_ignore_control
 dw terminal_control_4cd7
 dw terminal_control_0e7c
 dw terminal_control_0ede
 dw terminal_control_3778
 dw terminal_backspace
 dw terminal_tab
 dw terminal_linefeed
 dw terminal_control_0f62
 dw terminal_control_0fb0
 dw terminal_carriage_return
 dw terminal_control_1040
 dw terminal_control_1064
 dw terminal_control_1096
 dw terminal_ignore_control
 dw terminal_control_10ce
 dw terminal_control_10fc
 dw terminal_control_110a
 dw terminal_control_113e
 dw terminal_control_115c
 dw terminal_control_1190
 dw terminal_control_11a8
 dw terminal_control_123c
 dw terminal_control_1248
 dw terminal_ignore_control
 dw terminal_control_127e
 dw terminal_control_1292
 dw terminal_control_12b0
 dw screen_wrap_forward
