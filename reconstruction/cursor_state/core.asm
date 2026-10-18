; Recovered PCPlus2.01 save/restore services; not original source.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef CURSOR_STATE_OMF
SEGMENT _TEXT public class=CODE use16
global csi_save_cursor,csi_restore_cursor
extern screen_set_cursor
extern screen_cursor_row, screen_cursor_column, csi_saved_row, csi_saved_column, ansi_charset_g1_flag_graphics, ansi_charset_g0_flag_graphics, cursor_state_value_cdfc, cursor_state_value_ce04, attributes_current, cursor_state_value_1d20, csi_origin_mode, csi_wrap_pending, cursor_state_saved_cdf0, cursor_state_saved_cdec, cursor_state_saved_cdfc, cursor_state_saved_ce04, cursor_state_saved_1f70, cursor_state_saved_1d20, cursor_state_saved_cdd2, cursor_state_saved_3342
%else
ORG 0xdd74
%define screen_set_cursor 0x1bbe
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define csi_saved_row 0x334e
%define csi_saved_column 0x3350
%define ansi_charset_g1_flag_graphics 0xcdf0
%define ansi_charset_g0_flag_graphics 0xcdec
%define cursor_state_value_cdfc 0xcdfc
%define cursor_state_value_ce04 0xce04
%define attributes_current 0x1f70
%define cursor_state_value_1d20 0x1d20
%define csi_origin_mode 0xcdd2
%define csi_wrap_pending 0x3342
%define cursor_state_saved_cdf0 0xcc96
%define cursor_state_saved_cdec 0xcc48
%define cursor_state_saved_cdfc 0xcbb0
%define cursor_state_saved_ce04 0xcbb4
%define cursor_state_saved_1f70 0xcdd4
%define cursor_state_saved_1d20 0xcd24
%define cursor_state_saved_cdd2 0xcd2c
%define cursor_state_saved_3342 0xd110
%endif
csi_save_cursor:
L_dd74: push bp
L_dd75: mov_load bp, sp
L_dd77: mov ax, [screen_cursor_row]
L_dd7a: mov [csi_saved_row], ax
L_dd7d: mov ax, [screen_cursor_column]
L_dd80: mov [csi_saved_column], ax
L_dd83: cmp word [bp + 0x4], 0x0
L_dd87: jnz L_ddb9
L_dd89: mov ax, [ansi_charset_g1_flag_graphics]
L_dd8c: mov [cursor_state_saved_cdf0], ax
L_dd8f: mov ax, [ansi_charset_g0_flag_graphics]
L_dd92: mov [cursor_state_saved_cdec], ax
L_dd95: mov ax, [cursor_state_value_cdfc]
L_dd98: mov [cursor_state_saved_cdfc], ax
L_dd9b: mov ax, [cursor_state_value_ce04]
L_dd9e: mov [cursor_state_saved_ce04], ax
L_dda1: mov ax, [attributes_current]
L_dda4: mov [cursor_state_saved_1f70], ax
L_dda7: mov ax, [cursor_state_value_1d20]
L_ddaa: mov [cursor_state_saved_1d20], ax
L_ddad: mov ax, [csi_origin_mode]
L_ddb0: mov [cursor_state_saved_cdd2], ax
L_ddb3: mov ax, [csi_wrap_pending]
L_ddb6: mov [cursor_state_saved_3342], ax
L_ddb9: pop bp
L_ddba: ret
nop ; original alignment instruction
csi_restore_cursor:
L_ddbc: push bp
L_ddbd: mov_load bp, sp
L_ddbf: mov ax, [csi_saved_row]
L_ddc2: mov dx, word [csi_saved_column]
L_ddc6: call screen_set_cursor
L_ddc9: cmp word [bp + 0x4], 0x0
L_ddcd: jnz L_ddff
L_ddcf: mov ax, [cursor_state_saved_cdf0]
L_ddd2: mov [ansi_charset_g1_flag_graphics], ax
L_ddd5: mov ax, [cursor_state_saved_cdec]
L_ddd8: mov [ansi_charset_g0_flag_graphics], ax
L_dddb: mov ax, [cursor_state_saved_cdfc]
L_ddde: mov [cursor_state_value_cdfc], ax
L_dde1: mov ax, [cursor_state_saved_ce04]
L_dde4: mov [cursor_state_value_ce04], ax
L_dde7: mov ax, [cursor_state_saved_1f70]
L_ddea: mov [attributes_current], ax
L_dded: mov ax, [cursor_state_saved_1d20]
L_ddf0: mov [cursor_state_value_1d20], ax
L_ddf3: mov ax, [cursor_state_saved_cdd2]
L_ddf6: mov [csi_origin_mode], ax
L_ddf9: mov ax, [cursor_state_saved_3342]
L_ddfc: mov [csi_wrap_pending], ax
L_ddff: mov_load sp, bp
L_de01: pop bp
L_de02: ret
nop ; original alignment instruction
