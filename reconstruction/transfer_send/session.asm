; Exact original sender instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SEND_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global transfer_send_session
global send_at_de59
global send_at_de5b
global send_at_de5e
global send_at_de5f
global send_at_de60
global send_at_de63
global send_at_de66
global send_at_de69
global send_at_de6c
global send_at_de6d
global send_at_de6e
global send_at_de71
global send_at_de73
global send_at_de75
global send_at_de77
global send_at_de79
global send_at_de7b
global send_at_de7d
global send_at_de7f
global send_at_de81
global send_at_de83
global send_at_de86
global send_at_de89
global send_at_de8c
global send_at_de8e
global send_at_de90
global send_at_de92
global send_at_de94
global send_at_de96
global send_at_de98
global send_at_de9b
global send_at_de9d
global send_at_de9e
global send_at_dea0
global send_at_dea2
global send_at_dea4
global send_at_dea6
global send_at_dea8
global send_at_dead
global send_at_deaf
global send_at_deb2
global send_at_deb3
global send_at_deb6
global send_at_deb9
global send_at_deba
global send_at_debb
global send_at_debd
global send_at_debe
global send_at_debf
global send_at_dec0
global send_at_dec3
global send_at_dec4
global send_at_dec7
global send_at_dec8
global send_at_decb
global send_at_dece
global send_at_ded1
global send_at_ded3
global send_at_ded5
global send_at_ded8
global send_at_ded9
global send_at_dedc
global send_at_dedf
global send_at_dee1
global send_at_dee2
global send_at_dee3
global send_at_dee5
global send_at_dee6
global send_at_dee7
global send_at_dee8
global send_at_deeb
global send_at_deec
global send_at_def0
global send_at_def3
global send_at_def6
global send_at_def9
global send_at_defa
global send_at_defd
global send_at_df00
global send_at_df01
global send_at_df04
global send_at_df07
global send_at_df0c
global send_at_df11
global send_at_df17
global send_at_df1a
global send_at_df1e
global send_at_df23
global send_at_df25
global send_at_df2a
global send_at_df2c
global send_at_df31
global send_at_df33
global send_at_df38
global send_at_df3a
global send_at_df3c
global send_at_df42
global send_at_df44
global send_at_df4a
global send_at_df4d
global send_at_df50
global send_at_df51
global send_at_df54
global send_at_df57
global send_at_df59
global send_at_df5b
global send_at_df5d
global send_at_df60
global send_at_df62
global send_at_df64
global send_at_df67
global send_at_df68
global send_at_df6b
global send_at_df6d
global send_at_df70
global send_at_df73
global send_at_df76
global send_at_df79
global send_at_df7e
global send_at_df81
global send_at_df84
global send_at_df87
global send_at_df89
global send_at_df8c
global send_at_df8e
global send_at_df91
global send_at_df93
global send_at_df96
global send_at_df97
global send_at_df9a
global send_at_df9c
global send_at_df9e
global send_at_dfa0
global send_at_dfa3
global send_at_dfa5
global send_at_dfa7
global send_at_dfaa
global send_at_dfab
global send_at_dfae
global send_at_dfaf
global send_at_dfb2
global send_at_dfb5
global send_at_dfb8
global send_at_dfba
global send_at_dfbc
global send_at_dfbf
global send_at_dfc0
global send_at_dfc3
global send_at_dfc4
global send_at_dfc7
global send_at_dfca
global send_at_dfcb
global send_at_dfce
global send_at_dfd0
global send_at_dfd1
global send_at_dfd4
global send_at_dfd7
global send_at_dfd9
global send_at_dfdc
global send_at_dfde
global send_at_dfe0
global send_at_dfe2
global send_at_dfe4
global send_at_dfe6
global send_at_dfe8
global send_at_dfea
global send_at_dfec
global send_at_dfee
global send_at_dff0
global send_at_dff2
global send_at_dff7
global send_at_dff9
global send_at_dffa
global send_at_dfff
global send_at_e003
global send_at_e005
global send_at_e009
global send_at_e00b
global send_at_e00e
global send_at_e011
global send_at_e012
global send_at_e015
global send_at_e016
global send_at_e019
global send_at_e01c
global send_at_e01f
global send_at_e020
global send_at_e023
global send_at_e024
global send_at_e025
global send_at_e027
global send_at_e028
global send_at_e029
global send_at_e02a
global send_at_e02d
global send_at_e02e
global send_at_e02f
global send_at_e031
global send_at_e032
global send_at_e033
global send_at_e034
global send_at_e037
global send_at_e03c
global send_at_e03e
global send_at_e041
global send_at_e042
global send_at_e046
global send_at_e049
global send_at_e04b
global send_at_e04f
global send_at_e052
global send_at_e056
global send_at_e059
global send_at_e05c
global send_at_e061
global send_at_e063
global send_at_e066
global send_at_e069
global send_at_e06c
global send_at_e06e
global send_at_e070
global send_at_e072
global send_at_e077
global send_at_e079
global send_at_e07e
global send_at_e080
global send_at_e083
global send_at_e086
global send_at_e089
global send_at_e08b
global send_at_e08d
global send_at_e090
global send_at_e093
global send_at_e094
global send_at_e097
global send_at_e098
global send_at_e09b
global send_at_e09d
global send_at_e0a0
global send_at_e0a2
global send_at_e0a5
global send_at_e0a7
global send_at_e0aa
global send_at_e0ad
global send_at_e0ae
global send_at_e0b1
global send_at_e0b2
global send_at_e0b5
global send_at_e0b8
global send_at_e0bb
global send_at_e0be
global send_at_e0c1
global send_at_e0c5
global send_at_e0c8
global send_at_e0ca
global send_at_e0cb
global send_at_e0cc
global send_at_e0ce
global send_at_e0d2
global send_at_e0d5
global send_at_e0d6
global send_at_e0d9
global send_at_e0da
global send_at_e0db
global send_at_e0de
global send_at_e0e1
global send_at_e0e3
global send_at_e0e5
global send_at_e0e7
global send_at_e0ea
global send_at_e0ec
global send_at_e0ee
global send_at_e0f1
global send_at_e0f4
global send_at_e0fa
global send_at_e0ff
global send_at_e102
global send_at_e104
global send_at_e106
global send_at_e109
global send_at_e10a
global send_at_e10d
global send_at_e10e
global send_at_e111
global send_at_e114
global send_at_e117
global send_at_e119
global send_at_e11b
global send_at_e11e
global send_at_e11f
global send_at_e122
global send_at_e123
global send_at_e126
global send_at_e129
global send_at_e12c
global send_at_e12f
global send_at_e132
global send_at_e136
global send_at_e139
global send_at_e13c
global send_at_e13e
global send_at_e13f
global send_at_e142
global send_at_e147
global send_at_e14a
global send_at_e14e
global send_at_e14f
global send_at_e153
global send_at_e156
global send_at_e15a
global send_at_e15c
global send_at_e160
global send_at_e162
global send_at_e166
global send_at_e169
global send_at_e16b
global send_at_e16d
global send_at_e170
global send_at_e174
global send_at_e176
global send_at_e177
global send_at_e179
global send_at_e17a
global send_at_e17d
global send_at_e17f
global send_at_e181
global send_at_e182
global send_at_e184
global send_at_e187
global send_at_e189
global send_at_e18a
global send_at_e18e
global send_at_e191
global send_at_e195
global send_at_e196
global send_at_e199
global send_at_e19c
global send_at_e19e
global send_at_e1a0
global send_at_e1a2
global send_at_e1a5
global send_at_e1a7
global send_at_e1ab
global send_at_e1ac
global send_at_e1af
global send_at_e1b3
global send_at_e1b6
global send_at_e1bb
global send_at_e1bd
global send_at_e1c0
global send_at_e1c3
global send_at_e1c6
global send_at_e1c7
global send_at_e1ca
global send_at_e1cc
global send_at_e1cf
global send_at_e1d1
global send_at_e1d2
global send_at_e1d5
global send_at_e1d8
global send_at_e1dc
global send_at_e1df
global send_at_e1e0
global send_at_e1e3
global send_at_e1e6
global send_at_e1e9
global send_at_e1eb
global send_at_e1ef
global send_at_e1f1
global send_at_e1f4
global send_at_e1f8
global send_at_e1fb
global send_at_e1ff
global send_at_e200
global send_at_e204
global send_at_e208
global send_at_e20c
global send_at_e210
global send_at_e213
global send_at_e217
global send_at_e21c
global send_at_e21e
global send_at_e221
global send_at_e225
global send_at_e229
global send_at_e22d
global send_at_e22f
global send_at_e231
global send_at_e233
global send_at_e236
global send_at_e238
global send_at_e23e
global send_at_e243
global send_at_e246
global send_at_e24a
global send_at_e24c
global send_at_e250
global send_at_e252
global send_at_e255
global send_at_e259
global send_at_e25b
global send_at_e25e
global send_at_e262
global send_at_e265
global send_at_e268
global send_at_e26c
global send_at_e26e
global send_at_e270
global send_at_e273
global send_at_e274
global send_at_e279
global send_at_e27b
global send_at_e27e
global send_at_e281
global send_at_e282
global send_at_e285
global send_at_e288
global send_at_e28b
global send_at_e28c
global send_at_e28f
global send_at_e290
global send_at_e293
global send_at_e296
global send_at_e29a
global send_at_e29d
global send_at_e2a0
global send_at_e2a3
global send_at_e2a6
global send_at_e2a7
global send_at_e2aa
global send_at_e2ad
global send_at_e2ae
global send_at_e2b1
global send_at_e2b2
global send_at_e2b4
global send_at_e2b7
global send_at_e2ba
global send_at_e2bd
global send_at_e2bf
global send_at_e2c0
global send_at_e2c2
global send_at_e2c4
global send_at_e2c6
global send_at_e2c9
global send_at_e2cc
global send_at_e2cd
global send_at_e2ce
global send_at_e2d0
global send_at_e2d1
extern send_ui_context
extern send_integrity_labels
extern send_protocol
extern send_buffer_pointer
extern send_filename_display
extern send_local_cancel
extern send_carrier
extern _transfer_crc_buffer_original
extern send_display_text
extern send_initial_open_mode
extern send_binary_open_mode
extern send_close_file
extern send_open_file
extern send_read_file
extern send_queued_count
extern send_total_low
extern send_total_high
extern send_file_size_low
extern send_file_size_high
extern send_checkpoint
extern send_unwind
extern send_receive_byte
extern send_timed_byte
extern send_transmit_byte
extern send_transmit_buffer
extern send_flush_input
extern send_session_low
extern send_session_high
extern send_block_size
extern send_file_handle
extern send_crc_high
extern send_crc_low
extern send_block_number
extern send_buffer_used
extern send_blocks_counted
extern send_error_count
extern send_checkpoint_buffer
extern send_streaming_mode
extern send_directory_prefix
extern send_delegate_U
extern send_delegate_protocol13
extern send_delegate_W
extern send_reset_state
extern send_progress
extern send_status
extern send_metadata3
extern send_metadata5
extern send_display_start
extern send_prepare_ui
extern send_control_status
extern send_initialize_progress
%else
ORG 0xde58
%define send_ui_context 0x1f76
%define send_integrity_labels 0x2e44
%define send_protocol 0x3996
%define send_buffer_pointer 0x39c0
%define send_filename_display 0x3ea4
%define send_local_cancel 0x3f4b
%define send_carrier 0x4861
%define _transfer_crc_buffer_original 0x5c77
%define send_display_text 0x6bf0
%define send_initial_open_mode 0x77f3
%define send_binary_open_mode 0x77f6
%define send_close_file 0x8318
%define send_open_file 0x841a
%define send_read_file 0x845a
%define send_queued_count 0x8e20
%define send_total_low 0x8ffa
%define send_total_high 0x8ffc
%define send_file_size_low 0x9006
%define send_file_size_high 0x9008
%define send_checkpoint 0x9048
%define send_unwind 0x9065
%define send_receive_byte 0xaa65
%define send_timed_byte 0xaad9
%define send_transmit_byte 0xab0b
%define send_transmit_buffer 0xab92
%define send_flush_input 0xabca
%define send_session_low 0xcb2c
%define send_session_high 0xcb2e
%define send_block_size 0xcb5e
%define send_file_handle 0xcbaa
%define send_crc_high 0xcbae
%define send_crc_low 0xcbb2
%define send_block_number 0xcc9a
%define send_buffer_used 0xcd34
%define send_blocks_counted 0xcd80
%define send_error_count 0xcd8a
%define send_checkpoint_buffer 0xcd94
%define send_streaming_mode 0xcdcc
%define send_directory_prefix 0xceea
%define send_delegate_U 0xd083
%define send_delegate_protocol13 0xd08f
%define send_delegate_W 0xd0a7
%define send_reset_state 0xd656
%define send_progress 0xe322
%define send_status 0xe498
%define send_metadata3 0xe5da
%define send_metadata5 0xe762
%define send_display_start 0xee10
%define send_prepare_ui 0xefb0
%define send_control_status 0xf050
%define send_initialize_progress 0xf0d4
%endif
%include "encodings.inc"
transfer_send_session: push bp
send_at_de59: mov_load bp,sp
send_at_de5b: sub sp,0x50
send_at_de5e: push di
send_at_de5f: push si
send_at_de60: call send_reset_state
send_at_de63: call send_prepare_ui
send_at_de66: mov di,send_directory_prefix
send_at_de69: lea si,[bp-0x4e]
send_at_de6c: push ds
send_at_de6d: pop es
send_at_de6e: mov cx,0xffff
send_at_de71: xor_load ax,ax
send_at_de73: repne scasb
send_at_de75: not cx
send_at_de77: sub_load di,cx
send_at_de79: xchg di,si
send_at_de7b: shr cx,1
send_at_de7d: rep movsw
send_at_de7f: adc_load cx,cx
send_at_de81: rep movsb
send_at_de83: lea si,[bp-0x4e]
send_at_de86: mov di,[bp+0x4]
send_at_de89: mov cx,0xffff
send_at_de8c: xor_load ax,ax
send_at_de8e: repne scasb
send_at_de90: not cx
send_at_de92: sub_load di,cx
send_at_de94: mov_load bx,cx
send_at_de96: xchg di,si
send_at_de98: mov cx,0xffff
send_at_de9b: repne scasb
send_at_de9d: dec di
send_at_de9e: mov_load cx,bx
send_at_dea0: shr cx,1
send_at_dea2: rep movsw
send_at_dea4: adc_load cx,cx
send_at_dea6: rep movsb
send_at_dea8: cmp word [send_protocol],0xd
send_at_dead: jnz short send_at_dec0
send_at_deaf: lea ax,[bp-0x4e]
send_at_deb2: push ax
send_at_deb3: call send_delegate_protocol13
send_at_deb6: add sp,0x2
send_at_deb9: pop si
send_at_deba: pop di
send_at_debb: mov_load sp,bp
send_at_debd: pop bp
send_at_debe: ret
send_at_debf: nop
send_at_dec0: mov ax,send_initial_open_mode
send_at_dec3: push ax
send_at_dec4: lea ax,[bp-0x4e]
send_at_dec7: push ax
send_at_dec8: call send_open_file
send_at_decb: add sp,0x4
send_at_dece: mov [send_file_handle],ax
send_at_ded1: or_load ax,ax
send_at_ded3: jnz short send_at_dee8
send_at_ded5: mov ax,0xd
send_at_ded8: push ax
send_at_ded9: call send_status
send_at_dedc: add sp,0x2
send_at_dedf: sub_load ax,ax
send_at_dee1: pop si
send_at_dee2: pop di
send_at_dee3: mov_load sp,bp
send_at_dee5: pop bp
send_at_dee6: ret
send_at_dee7: nop
send_at_dee8: mov ax,0x73e
send_at_deeb: push ax
send_at_deec: push word [send_ui_context]
send_at_def0: push word [bp+0x4]
send_at_def3: call send_filename_display
send_at_def6: add sp,0x2
send_at_def9: push ax
send_at_defa: call send_display_text
send_at_defd: mov ax,0x1
send_at_df00: push ax
send_at_df01: call send_display_start
send_at_df04: add sp,0x2
send_at_df07: mov word [bp-0x4],0x0
send_at_df0c: mov word [bp-0x6],0x0
send_at_df11: mov word [send_block_size],0x80
send_at_df17: mov di,0x1
send_at_df1a: mov [send_block_number],di
send_at_df1e: cmp word [send_protocol],0x2
send_at_df23: jz short send_at_df33
send_at_df25: cmp word [send_protocol],0x5
send_at_df2a: jz short send_at_df33
send_at_df2c: cmp word [send_streaming_mode],0x0
send_at_df31: jz short send_at_df4d
send_at_df33: cmp word [send_file_size_high],0x0
send_at_df38: jl short send_at_df4d
send_at_df3a: jg short send_at_df44
send_at_df3c: cmp word [send_file_size_low],0x400
send_at_df42: jc short send_at_df4d
send_at_df44: mov word [send_block_size],0x400
send_at_df4a: mov di,0x2
send_at_df4d: mov ax,send_checkpoint_buffer
send_at_df50: push ax
send_at_df51: call send_checkpoint
send_at_df54: add sp,0x2
send_at_df57: mov_load si,ax
send_at_df59: or_load si,si
send_at_df5b: jz short send_at_df76
send_at_df5d: cmp si,0x1
send_at_df60: jnz short send_at_df68
send_at_df62: sub_load ax,ax
send_at_df64: jmp near send_at_e28f
send_at_df67: nop
send_at_df68: cmp si,0xf
send_at_df6b: jnz short send_at_df70
send_at_df6d: jmp near send_at_e28f
send_at_df70: mov ax,0xb
send_at_df73: jmp near send_at_e28f
send_at_df76: mov [bp-0xc],di
send_at_df79: mov word [bp-0x8],0x2
send_at_df7e: mov ax,[bp-0x4]
send_at_df81: inc word [bp-0x4]
send_at_df84: cmp ax,strict word 0xf
send_at_df87: jc short send_at_df8c
send_at_df89: jmp near send_at_e034
send_at_df8c: sub_load dx,dx
send_at_df8e: mov [bp-0x2],dx
send_at_df91: mov_load si,dx
send_at_df93: mov ax,0x1
send_at_df96: push ax
send_at_df97: call send_timed_byte
send_at_df9a: mov_load di,ax
send_at_df9c: or_load di,di
send_at_df9e: jnl short send_at_dfd0
send_at_dfa0: call send_local_cancel
send_at_dfa3: or_load ax,ax
send_at_dfa5: jz short send_at_dfb5
send_at_dfa7: mov ax,0x7
send_at_dfaa: push ax
send_at_dfab: mov ax,send_checkpoint_buffer
send_at_dfae: push ax
send_at_dfaf: call send_unwind
send_at_dfb2: add sp,0x4
send_at_dfb5: call send_carrier
send_at_dfb8: or_load ax,ax
send_at_dfba: jnz short send_at_dfca
send_at_dfbc: mov ax,0xf
send_at_dfbf: push ax
send_at_dfc0: mov ax,send_checkpoint_buffer
send_at_dfc3: push ax
send_at_dfc4: call send_unwind
send_at_dfc7: add sp,0x4
send_at_dfca: inc si
send_at_dfcb: cmp si,0xa
send_at_dfce: jc short send_at_df93
send_at_dfd0: push di
send_at_dfd1: call send_control_status
send_at_dfd4: add sp,0x2
send_at_dfd7: mov_load ax,di
send_at_dfd9: cmp ax,strict word 0x57
send_at_dfdc: jz short send_at_e02a
send_at_dfde: ja short send_at_dfff
send_at_dfe0: sub al,0x15
send_at_dfe2: jz short send_at_dff2
send_at_dfe4: sub al,0x2e
send_at_dfe6: jz short send_at_dffa
send_at_dfe8: sub al,0x4
send_at_dfea: jz short send_at_dffa
send_at_dfec: sub al,0xe
send_at_dfee: jz short send_at_e020
send_at_dff0: jmp short send_at_dfff
send_at_dff2: mov word [bp-0x8],0x0
send_at_dff7: jmp short send_at_dfff
send_at_dff9: nop
send_at_dffa: mov word [bp-0x8],0x1
send_at_dfff: cmp word [bp-0x8],0x2
send_at_e003: jl short send_at_e034
send_at_e005: cmp word [bp-0x4],0xf
send_at_e009: jnc short send_at_e00e
send_at_e00b: jmp near send_at_df7e
send_at_e00e: mov ax,0x1
send_at_e011: push ax
send_at_e012: mov ax,send_checkpoint_buffer
send_at_e015: push ax
send_at_e016: call send_unwind
send_at_e019: add sp,0x4
send_at_e01c: jmp near send_at_df7e
send_at_e01f: nop
send_at_e020: call send_delegate_U
send_at_e023: pop si
send_at_e024: pop di
send_at_e025: mov_load sp,bp
send_at_e027: pop bp
send_at_e028: ret
send_at_e029: nop
send_at_e02a: call send_delegate_W
send_at_e02d: pop si
send_at_e02e: pop di
send_at_e02f: mov_load sp,bp
send_at_e031: pop bp
send_at_e032: ret
send_at_e033: nop
send_at_e034: call send_flush_input
send_at_e037: cmp word [send_streaming_mode],0x0
send_at_e03c: jnz short send_at_e052
send_at_e03e: mov ax,0x93e
send_at_e041: push ax
send_at_e042: push word [send_ui_context]
send_at_e046: mov bx,[bp-0x8]
send_at_e049: shl bx,1
send_at_e04b: push word [bx+send_integrity_labels]
send_at_e04f: call send_display_text
send_at_e052: push word [send_file_handle]
send_at_e056: call send_close_file
send_at_e059: add sp,0x2
send_at_e05c: cmp word [send_protocol],0x3
send_at_e061: jnz short send_at_e072
send_at_e063: push word [bp+0x4]
send_at_e066: call send_metadata3
send_at_e069: add sp,0x2
send_at_e06c: or_load ax,ax
send_at_e06e: jnz short send_at_e0aa
send_at_e070: jmp short send_at_e08d
send_at_e072: cmp word [send_protocol],0x5
send_at_e077: jz short send_at_e080
send_at_e079: cmp word [send_protocol],0xb
send_at_e07e: jnz short send_at_e0aa
send_at_e080: push word [bp+0x4]
send_at_e083: call send_metadata5
send_at_e086: add sp,0x2
send_at_e089: or_load ax,ax
send_at_e08b: jnz short send_at_e094
send_at_e08d: mov ax,0xa
send_at_e090: jmp near send_at_ded8
send_at_e093: nop
send_at_e094: mov ax,0xa
send_at_e097: push ax
send_at_e098: call send_timed_byte
send_at_e09b: mov_load si,ax
send_at_e09d: cmp si,0x43
send_at_e0a0: jz short send_at_e0aa
send_at_e0a2: cmp si,0x47
send_at_e0a5: jz short send_at_e0aa
send_at_e0a7: jmp near send_at_e26e
send_at_e0aa: mov ax,send_binary_open_mode
send_at_e0ad: push ax
send_at_e0ae: lea ax,[bp-0x4e]
send_at_e0b1: push ax
send_at_e0b2: call send_open_file
send_at_e0b5: add sp,0x4
send_at_e0b8: mov [send_file_handle],ax
send_at_e0bb: call send_initialize_progress
send_at_e0be: mov ax,0x1a
send_at_e0c1: mov dx,[send_buffer_pointer]
send_at_e0c5: mov cx,0x2800
send_at_e0c8: mov_load di,dx
send_at_e0ca: push ds
send_at_e0cb: pop es
send_at_e0cc: rep stosb
send_at_e0ce: push word [send_file_handle]
send_at_e0d2: mov ax,0x2800
send_at_e0d5: push ax
send_at_e0d6: mov ax,0x1
send_at_e0d9: push ax
send_at_e0da: push dx
send_at_e0db: call send_read_file
send_at_e0de: add sp,0x8
send_at_e0e1: mov_load si,ax
send_at_e0e3: or_load si,si
send_at_e0e5: jnz short send_at_e0ea
send_at_e0e7: jmp near send_at_e25e
send_at_e0ea: or_load si,si
send_at_e0ec: jnl short send_at_e0f1
send_at_e0ee: jmp near send_at_e28c
send_at_e0f1: mov [bp-0xa],si
send_at_e0f4: mov word [send_buffer_used],0x0
send_at_e0fa: mov word [bp-0x6],0x0
send_at_e0ff: call send_local_cancel
send_at_e102: or_load ax,ax
send_at_e104: jz short send_at_e114
send_at_e106: mov ax,0x7
send_at_e109: push ax
send_at_e10a: mov ax,send_checkpoint_buffer
send_at_e10d: push ax
send_at_e10e: call send_unwind
send_at_e111: add sp,0x4
send_at_e114: call send_carrier
send_at_e117: or_load ax,ax
send_at_e119: jnz short send_at_e129
send_at_e11b: mov ax,0xf
send_at_e11e: push ax
send_at_e11f: mov ax,send_checkpoint_buffer
send_at_e122: push ax
send_at_e123: call send_unwind
send_at_e126: add sp,0x4
send_at_e129: call send_flush_input
send_at_e12c: push word [bp-0xc]
send_at_e12f: call send_transmit_byte
send_at_e132: push word [send_block_number]
send_at_e136: call send_transmit_byte
send_at_e139: mov ax,[send_block_number]
send_at_e13c: not ax
send_at_e13e: push ax
send_at_e13f: call send_transmit_byte
send_at_e142: mov word [bp-0x2],0x0
send_at_e147: mov ax,[send_buffer_used]
send_at_e14a: add ax,[send_buffer_pointer]
send_at_e14e: push ax
send_at_e14f: push word [send_block_size]
send_at_e153: call send_transmit_buffer
send_at_e156: cmp word [bp-0x8],0x0
send_at_e15a: jnz short send_at_e18a
send_at_e15c: mov si,[send_buffer_used]
send_at_e160: mov_load ax,si
send_at_e162: add ax,[send_block_size]
send_at_e166: mov [bp-0x50],ax
send_at_e169: cmp_load ax,si
send_at_e16b: jna short send_at_e184
send_at_e16d: mov dx,[bp-0x2]
send_at_e170: mov bx,[send_buffer_pointer]
send_at_e174: mov al,[bx+si]
send_at_e176: cbw
send_at_e177: add_load dx,ax
send_at_e179: inc si
send_at_e17a: cmp [bp-0x50],si
send_at_e17d: ja short send_at_e170
send_at_e17f: sub_load dh,dh
send_at_e181: push dx
send_at_e182: jmp short send_at_e1b3
send_at_e184: mov dx,[bp-0x2]
send_at_e187: jmp short send_at_e17f
send_at_e189: nop
send_at_e18a: push word [send_block_size]
send_at_e18e: mov ax,[send_buffer_used]
send_at_e191: add ax,[send_buffer_pointer]
send_at_e195: push ax
send_at_e196: call _transfer_crc_buffer_original
send_at_e199: add sp,0x4
send_at_e19c: mov_load cx,ax
send_at_e19e: mov_load al,ah
send_at_e1a0: sub_load ah,ah
send_at_e1a2: mov [send_crc_high],ax
send_at_e1a5: sub_load ch,ch
send_at_e1a7: mov [send_crc_low],cx
send_at_e1ab: push ax
send_at_e1ac: call send_transmit_byte
send_at_e1af: push word [send_crc_low]
send_at_e1b3: call send_transmit_byte
send_at_e1b6: cmp word [send_streaming_mode],0x0
send_at_e1bb: jz short send_at_e1c0
send_at_e1bd: jmp near send_at_e274
send_at_e1c0: inc word [bp-0x6]
send_at_e1c3: mov ax,0xa
send_at_e1c6: push ax
send_at_e1c7: call send_timed_byte
send_at_e1ca: mov_load si,ax
send_at_e1cc: cmp si,0x6
send_at_e1cf: jz short send_at_e1e6
send_at_e1d1: push si
send_at_e1d2: call send_control_status
send_at_e1d5: add sp,0x2
send_at_e1d8: inc word [send_error_count]
send_at_e1dc: mov ax,0x9
send_at_e1df: push ax
send_at_e1e0: call send_status
send_at_e1e3: add sp,0x2
send_at_e1e6: cmp si,0x6
send_at_e1e9: jz short send_at_e1f4
send_at_e1eb: cmp word [bp-0x6],0xf
send_at_e1ef: jz short send_at_e1f4
send_at_e1f1: jmp near send_at_e0ff
send_at_e1f4: inc word [send_blocks_counted]
send_at_e1f8: mov ax,[send_block_size]
send_at_e1fb: add [send_buffer_used],ax
send_at_e1ff: cwd
send_at_e200: add [send_total_low],ax
send_at_e204: adc [send_total_high],dx
send_at_e208: add [send_session_low],ax
send_at_e20c: adc [send_session_high],dx
send_at_e210: call send_progress
send_at_e213: inc word [send_block_number]
send_at_e217: cmp word [send_protocol],0x4
send_at_e21c: jz short send_at_e243
send_at_e21e: mov ax,[send_file_size_low]
send_at_e221: mov dx,[send_file_size_high]
send_at_e225: sub ax,[send_total_low]
send_at_e229: sbb dx,[send_total_high]
send_at_e22d: or_load dx,dx
send_at_e22f: jg short send_at_e243
send_at_e231: jl short send_at_e238
send_at_e233: cmp ax,0x381
send_at_e236: jnc short send_at_e243
send_at_e238: mov word [send_block_size],0x80
send_at_e23e: mov word [bp-0xc],0x1
send_at_e243: mov ax,[bp-0xa]
send_at_e246: cmp [send_buffer_used],ax
send_at_e24a: jnc short send_at_e255
send_at_e24c: cmp word [bp-0x6],0xf
send_at_e250: jz short send_at_e255
send_at_e252: jmp near send_at_e0fa
send_at_e255: cmp word [bp-0x6],0xf
send_at_e259: jz short send_at_e25e
send_at_e25b: jmp near send_at_e0be
send_at_e25e: push word [send_file_handle]
send_at_e262: call send_close_file
send_at_e265: add sp,0x2
send_at_e268: cmp word [bp-0x6],0xf
send_at_e26c: jnz short send_at_e2a0
send_at_e26e: sub_load ax,ax
send_at_e270: jmp near send_at_ded8
send_at_e273: nop
send_at_e274: cmp word [send_queued_count],0x0
send_at_e279: jnz short send_at_e27e
send_at_e27b: jmp near send_at_e1f4
send_at_e27e: call send_receive_byte
send_at_e281: push ax
send_at_e282: call send_control_status
send_at_e285: add sp,0x2
send_at_e288: jmp near send_at_e1f4
send_at_e28b: nop
send_at_e28c: mov ax,0x4
send_at_e28f: push ax
send_at_e290: call send_status
send_at_e293: add sp,0x2
send_at_e296: push word [send_file_handle]
send_at_e29a: call send_close_file
send_at_e29d: jmp near send_at_dedc
send_at_e2a0: mov si,0xa
send_at_e2a3: mov ax,0x4
send_at_e2a6: push ax
send_at_e2a7: call send_transmit_byte
send_at_e2aa: mov ax,0xa
send_at_e2ad: push ax
send_at_e2ae: call send_timed_byte
send_at_e2b1: push ax
send_at_e2b2: mov_load di,ax
send_at_e2b4: call send_control_status
send_at_e2b7: add sp,0x2
send_at_e2ba: cmp di,0x6
send_at_e2bd: jz short send_at_e2c2
send_at_e2bf: dec si
send_at_e2c0: jnz short send_at_e2a3
send_at_e2c2: or_load si,si
send_at_e2c4: jg short send_at_e2c9
send_at_e2c6: jmp near send_at_dedf
send_at_e2c9: mov ax,0x1
send_at_e2cc: pop si
send_at_e2cd: pop di
send_at_e2ce: mov_load sp,bp
send_at_e2d0: pop bp
send_at_e2d1: ret
