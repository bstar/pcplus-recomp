; Exact original PCPlus2.01 connection commands and shared engine bodies.
; Component only: UI/serial/reset/KEY/META/persistence imports are explicit.
; DS=SS, DF=0. Native near RET/RETn, no ASIO ownership transition is invented.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CONNECTION_FLAT
%if ASPECT_CONNECTION_UNIT=1
ORG 0x567e
%elif ASPECT_CONNECTION_UNIT=2
ORG 0x5685
%elif ASPECT_CONNECTION_UNIT=3
ORG 0x568d
%elif ASPECT_CONNECTION_UNIT=4
ORG 0x5695
%elif ASPECT_CONNECTION_UNIT=5
ORG 0xe759
%elif ASPECT_CONNECTION_UNIT=6
ORG 0x445
%elif ASPECT_CONNECTION_UNIT=7
ORG 0xe182
%elif ASPECT_CONNECTION_UNIT=8
ORG 0xe20a
%elif ASPECT_CONNECTION_UNIT=9
ORG 0xe423
%elif ASPECT_CONNECTION_UNIT=10
ORG 0xe556
%elif ASPECT_CONNECTION_UNIT=11
ORG 0xe5e3
%else
%error Select ASPECT_CONNECTION_UNIT1..11
%endif
%define ac_call_adopt 0xe20a
%define ac_call_attempt 0xe8ad
%define ac_call_engine 0xcdb3
%define ac_call_flush 0xcd47
%define ac_call_hangup 0x445
%define ac_call_itoa 0x8e6c
%define ac_call_log 0xe2a9
%define ac_call_loop 0xe5e3
%define ac_call_manual 0xcff3
%define ac_call_optional 0xcd5f
%define ac_call_read_input 0xce1f
%define ac_call_read_second 0xce2b
%define ac_call_selection 0xcfe7
%define ac_call_service_03a7 0x3a7
%define ac_call_service_0cd2 0xcd2
%define ac_call_service_20a4 0x20a4
%define ac_call_service_2fb8 0x2fb8
%define ac_call_service_31bb 0x31bb
%define ac_call_service_36d4 0x36d4
%define ac_call_service_3fc7 0x3fc7
%define ac_call_service_4015 0x4015
%define ac_call_service_4056 0x4056
%define ac_call_service_48cc 0x48cc
%define ac_call_service_498b 0x498b
%define ac_call_service_6b42 0x6b42
%define ac_call_service_6b5a 0x6b5a
%define ac_call_service_6bb6 0x6bb6
%define ac_call_service_6bf0 0x6bf0
%define ac_call_service_6dca 0x6dca
%define ac_call_service_6e5a 0x6e5a
%define ac_call_service_75e8 0x75e8
%define ac_call_service_780e 0x780e
%define ac_call_service_8268 0x8268
%define ac_call_service_82a8 0x82a8
%define ac_call_service_8d18 0x8d18
%define ac_call_service_9128 0x9128
%define ac_call_service_97bc 0x97bc
%define ac_call_service_9888 0x9888
%define ac_call_service_aa5c 0xaa5c
%define ac_call_service_abca 0xabca
%define ac_call_service_adba 0xadba
%define ac_call_service_bae7 0xbae7
%define ac_call_service_da4e 0xda4e
%define ac_call_service_dd28 0xdd28
%define ac_call_service_dd94 0xdd94
%define ac_call_service_ddb6 0xddb6
%define ac_call_service_de19 0xde19
%define ac_call_service_dfcd 0xdfcd
%define ac_call_service_eaed 0xeaed
%define ac_call_service_eb89 0xeb89
%define ac_call_service_ec0e 0xec0e
%define ac_call_service_ec49 0xec49
%define ac_call_service_ec61 0xec61
%define ac_call_shared 0x5695
%define ac_baud 0x1b86
%define ac_call_count 0xe696
%define ac_call_date 0xe68d
%define ac_character_delay 0x1d68
%define ac_cycle_limit 0x1b9a
%define ac_data_1b8e 0x1b8e
%define ac_data_1b90 0x1b90
%define ac_data_1f7a 0x1f7a
%define ac_data_2076 0x2076
%define ac_data_6626 0x6626
%define ac_data_664c 0x664c
%define ac_data_6672 0x6672
%define ac_data_667c 0x667c
%define ac_data_6686 0x6686
%define ac_data_68b2 0x68b2
%define ac_data_69f0 0x69f0
%define ac_data_6f4a 0x6f4a
%define ac_data_6f50 0x6f50
%define ac_data_6ff2 0x6ff2
%define ac_data_bits 0x1b8c
%define ac_data_e464 0xe464
%define ac_data_e466 0xe466
%define ac_data_e468 0xe468
%define ac_data_e46a 0xe46a
%define ac_data_e57e 0xe57e
%define ac_data_e67e 0xe67e
%define ac_data_e680 0xe680
%define ac_data_e681 0xe681
%define ac_data_e682 0xe682
%define ac_data_e683 0xe683
%define ac_data_e684 0xe684
%define ac_data_e69a 0xe69a
%define ac_data_e6b8 0xe6b8
%define ac_data_e6c2 0xe6c2
%define ac_data_e6c4 0xe6c4
%define ac_data_e6c6 0xe6c6
%define ac_data_e6c8 0xe6c8
%define ac_data_e6ca 0xe6ca
%define ac_data_e6cc 0xe6cc
%define ac_data_e6ce 0xe6ce
%define ac_data_e6d0 0xe6d0
%define ac_driver_handle 0x8ff4
%define ac_duplex 0x1d1a
%define ac_empty 0x4942
%define ac_failure 0xd124
%define ac_hangup_dtr 0x1d72
%define ac_hangup_gate 0x1d78
%define ac_hangup_other_gate 0x3986
%define ac_hangup_text 0x1bfd
%define ac_key_name 0x21d8
%define ac_manual_name 0x69e4
%define ac_manual_token 0x7125
%define ac_meta_name 0x3262
%define ac_number 0xe669
%define ac_parity 0x1b88
%define ac_physical_rows 0x7a74
%define ac_port 0x1b84
%define ac_protocol 0x3996
%define ac_record 0xe650
%define ac_record_key 0xe6a6
%define ac_record_meta 0xe6af
%define ac_record_protocol 0xe698
%define ac_record_terminal 0xe699
%define ac_script_stream 0x4b02
%define ac_selection_end 0x711d
%define ac_selection_flag_end 0x7123
%define ac_selection_flags 0x70ba
%define ac_selections 0x70b4
%define ac_stop 0x1b8a
%define ac_terminal 0x1d18
%define ac_token_separators 0x7121
%else
%define ASPECT_CONNECTION_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_connection_dial
global aspect_connection_dial_commit
global aspect_connection_dial_engine
global aspect_connection_dial_loop
global aspect_connection_hangup
global aspect_connection_hangup_native
global aspect_connection_manual_record
global aspect_connection_mdial
global aspect_connection_redial
global aspect_connection_selection_list
global aspect_connection_shared
%define ac_call_adopt aspect_connection_dial_commit
%define ac_call_attempt modem_dial_attempt_original
extern modem_dial_attempt_original
%define ac_call_engine aspect_connection_dial_engine
%define ac_call_flush aspect_string_flush
extern aspect_string_flush
%define ac_call_hangup aspect_connection_hangup_native
%define ac_call_itoa aspect_conversion_itoa
extern aspect_conversion_itoa
%define ac_call_log ac_log
extern ac_log
%define ac_call_loop aspect_connection_dial_loop
%define ac_call_manual aspect_connection_manual_record
%define ac_call_optional aspect_string_option_flag
extern aspect_string_option_flag
%define ac_call_read_input aspect_string_read
extern aspect_string_read
%define ac_call_read_second aspect_string_read_destination
extern aspect_string_read_destination
%define ac_call_selection aspect_connection_selection_list
%define ac_call_service_03a7 ac_configure_serial
extern ac_configure_serial
%define ac_call_service_0cd2 ac_load_meta
extern ac_load_meta
%define ac_call_service_20a4 ac_terminal_reset
extern ac_terminal_reset
%define ac_call_service_2fb8 ac_status
extern ac_status
%define ac_call_service_31bb ac_message
extern ac_message
%define ac_call_service_36d4 ac_date
extern ac_date
%define ac_call_service_3fc7 ac_save_screen
extern ac_save_screen
%define ac_call_service_4015 ac_restore_screen
extern ac_restore_screen
%define ac_call_service_4056 ac_frame
extern ac_frame
%define ac_call_service_48cc ac_send_command
extern ac_send_command
%define ac_call_service_498b ac_format_time
extern ac_format_time
%define ac_call_service_6b42 ac_cursor_pop
extern ac_cursor_pop
%define ac_call_service_6b5a ac_cursor_push
extern ac_cursor_push
%define ac_call_service_6bb6 ac_delay
extern ac_delay
%define ac_call_service_6bf0 ac_draw_text
extern ac_draw_text
%define ac_call_service_6dca ac_cursor_show
extern ac_cursor_show
%define ac_call_service_6e5a ac_cursor_hide
extern ac_cursor_hide
%define ac_call_service_75e8 ac_printf_at
extern ac_printf_at
%define ac_call_service_780e ac_choices
extern ac_choices
%define ac_call_service_8268 ac_strcpy
extern ac_strcpy
%define ac_call_service_82a8 ac_driver_control
extern ac_driver_control
%define ac_call_service_8d18 ac_strlen
extern ac_strlen
%define ac_call_service_9128 ac_uppercase
extern ac_uppercase
%define ac_call_service_97bc ac_strtok
extern ac_strtok
%define ac_call_service_9888 ac_strncpy
extern ac_strncpy
%define ac_call_service_aa5c ac_carrier
extern ac_carrier
%define ac_call_service_abca ac_rx_flush
extern ac_rx_flush
%define ac_call_service_adba ac_close_port
extern ac_close_port
%define ac_call_service_bae7 ac_load_key
extern ac_load_key
%define ac_call_service_da4e ac_service_da4e
extern ac_service_da4e
%define ac_call_service_dd28 ac_write_stats
extern ac_write_stats
%define ac_call_service_dd94 ac_store_record
extern ac_store_record
%define ac_call_service_ddb6 ac_load_record
extern ac_load_record
%define ac_call_service_de19 ac_service_de19
extern ac_service_de19
%define ac_call_service_dfcd ac_service_dfcd
extern ac_service_dfcd
%define ac_call_service_eaed ac_service_eaed
extern ac_service_eaed
%define ac_call_service_eb89 ac_service_eb89
extern ac_service_eb89
%define ac_call_service_ec0e ac_abort_modem
extern ac_abort_modem
%define ac_call_service_ec49 ac_clear_selections
extern ac_clear_selections
%define ac_call_service_ec61 ac_expand_selection
extern ac_expand_selection
%define ac_call_shared aspect_connection_shared
extern ac_baud
extern ac_call_count
extern ac_call_date
extern ac_character_delay
extern ac_cycle_limit
extern ac_data_1b8e
extern ac_data_1b90
extern ac_data_1f7a
extern ac_data_2076
extern ac_data_6626
extern ac_data_664c
extern ac_data_6672
extern ac_data_667c
extern ac_data_6686
extern ac_data_68b2
extern ac_data_69f0
extern ac_data_6f4a
extern ac_data_6f50
extern ac_data_6ff2
extern ac_data_bits
extern ac_data_e464
extern ac_data_e466
extern ac_data_e468
extern ac_data_e46a
extern ac_data_e57e
extern ac_data_e67e
extern ac_data_e680
extern ac_data_e681
extern ac_data_e682
extern ac_data_e683
extern ac_data_e684
extern ac_data_e69a
extern ac_data_e6b8
extern ac_data_e6c2
extern ac_data_e6c4
extern ac_data_e6c6
extern ac_data_e6c8
extern ac_data_e6ca
extern ac_data_e6cc
extern ac_data_e6ce
extern ac_data_e6d0
extern ac_driver_handle
extern ac_duplex
extern ac_empty
extern ac_failure
extern ac_hangup_dtr
extern ac_hangup_gate
extern ac_hangup_other_gate
extern ac_hangup_text
extern ac_key_name
extern ac_manual_name
extern ac_manual_token
extern ac_meta_name
extern ac_number
extern ac_parity
extern ac_physical_rows
extern ac_port
extern ac_protocol
extern ac_record
extern ac_record_key
extern ac_record_meta
extern ac_record_protocol
extern ac_record_terminal
extern ac_script_stream
extern ac_selection_end
extern ac_selection_flag_end
extern ac_selection_flags
extern ac_selections
extern ac_stop
extern ac_terminal
extern ac_token_separators
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=1
; resident 0x567e; 7 original bytes.
aspect_connection_dial:
.L567e: sub_load ax,ax
.L5680: push ax
.L5681: call near ac_call_shared
.L5684: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=2
; resident 0x5685; 8 original bytes.
aspect_connection_mdial:
.L5685: mov ax,0x2
.L5688: push ax
.L5689: call near ac_call_shared
.L568c: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=3
; resident 0x568d; 8 original bytes.
aspect_connection_redial:
.L568d: mov ax,0x1
.L5690: push ax
.L5691: call near ac_call_shared
.L5694: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=4
; resident 0x5695; 105 original bytes.
aspect_connection_shared:
.L5695: push bp
.L5696: mov_load bp,sp
.L5698: sub sp,0x4
.L569b: push di
.L569c: push si
.L569d: mov si,[bp+0x4]
.L56a0: cmp si,0x1
.L56a3: jz .L56ac
.L56a5: call near ac_call_read_input
.L56a8: mov_load di,ax
.L56aa: jmp short .L56ae
.L56ac: sub_load di,di
.L56ae: cmp si,0x2
.L56b1: jnl .L56b8
.L56b3: mov ax,0x1
.L56b6: jmp short .L56ba
.L56b8: sub_load ax,ax
.L56ba: mov [bp-0x2],ax
.L56bd: push si
.L56be: push di
.L56bf: call near ac_call_optional
.L56c2: mov [bp-0x4],ax
.L56c5: or_load ax,ax
.L56c7: jz .L56ce
.L56c9: call near ac_call_read_second
.L56cc: jmp short .L56d0
.L56ce: sub_load ax,ax
.L56d0: push ax
.L56d1: call near ac_call_engine
.L56d4: mov_load si,ax
.L56d6: mov ax,[bp-0x4]
.L56d9: add ax,[bp-0x2]
.L56dc: cmp ax,strict word 0x2
.L56df: jnz .L56e4
.L56e1: call near ac_call_flush
.L56e4: test si,0x2
.L56e8: jz .L56ed
.L56ea: call near ac_call_service_bae7
.L56ed: mov_load ax,si
.L56ef: test al,0x4
.L56f1: jz .L56f6
.L56f3: call near ac_call_service_0cd2
.L56f6: pop si
.L56f7: pop di
.L56f8: mov_load sp,bp
.L56fa: pop bp
.L56fb: ret word 0x2
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=5
; 18 0xe759; 11 original bytes.
aspect_connection_hangup:
.Le759: mov ax,0x1
.Le75c: push ax
.Le75d: call near ac_call_hangup
.Le760: pop bx
.Le761: jmp near ac_call_service_2fb8
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=6
; resident 0x445; 131 original bytes.
aspect_connection_hangup_native:
.L0445: push bp
.L0446: mov_load bp,sp
.L0448: push si
.L0449: cmp word [ac_hangup_gate],0x0
.L044e: jz .L0457
.L0450: cmp word [ac_hangup_other_gate],0x0
.L0455: jnz .L04c3
.L0457: mov word [ac_failure],0x0
.L045d: call near ac_call_service_6b5a
.L0460: cmp word [bp+0x4],0x0
.L0464: jz .L0472
.L0466: sub_load ax,ax
.L0468: push ax
.L0469: push word [ac_data_2076]
.L046d: call near ac_call_service_31bb
.L0470: pop bx
.L0471: pop bx
.L0472: cmp word [ac_hangup_dtr],0x0
.L0477: jz .L0489
.L0479: mov ax,0xa
.L047c: push ax
.L047d: push word [ac_driver_handle]
.L0481: call near ac_call_service_82a8
.L0484: pop bx
.L0485: pop bx
.L0486: call near ac_call_service_6bb6
.L0489: call near ac_call_service_aa5c
.L048c: or_load ax,ax
.L048e: jz .L04ad
.L0490: mov si,[ac_character_delay]
.L0494: mov_load ax,si
.L0496: cmp ax,strict word 0x1e
.L0499: jnl .L049e
.L049b: mov ax,0x1e
.L049e: mov [ac_character_delay],ax
.L04a1: mov ax,ac_hangup_text
.L04a4: push ax
.L04a5: call near ac_call_service_48cc
.L04a8: pop bx
.L04a9: mov [ac_character_delay],si
.L04ad: call near ac_call_service_aa5c
.L04b0: or_load ax,ax
.L04b2: jz .L04ba
.L04b4: mov word [ac_failure],0x1
.L04ba: call near ac_call_service_03a7
.L04bd: call near ac_call_service_abca
.L04c0: call near ac_call_service_6b42
.L04c3: pop si
.L04c4: mov_load sp,bp
.L04c6: pop bp
.L04c7: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=7
; 4 0xe182; 136 original bytes.
aspect_connection_dial_engine:
.Le182: push bp
.Le183: mov_load bp,sp
.Le185: sub sp,0x2
.Le188: push di
.Le189: mov word [bp-0x2],0x0
.Le18e: call near ac_call_service_6e5a
.Le191: cmp word [ac_physical_rows],0x1c
.Le196: jng .Le19d
.Le198: call near ac_call_service_dfcd
.Le19b: jmp short .Le1a0
.Le19d: call near ac_call_service_de19
.Le1a0: cmp word [bp+0x8],0x2
.Le1a4: jnl .Le1d8
.Le1a6: cmp word [bp+0x8],0x0
.Le1aa: jnz .Le1b1
.Le1ac: mov ax,[bp+0x6]
.Le1af: jmp short .Le1b4
.Le1b1: mov ax,ac_empty
.Le1b4: push ax
.Le1b5: call near ac_call_selection
.Le1b8: pop bx
.Le1b9: mov_load di,ax
.Le1bb: push di
.Le1bc: call near ac_call_adopt
.Le1bf: mov [bp-0x2],ax
.Le1c2: cmp word [bp+0x4],0x0
.Le1c6: jz .Le1ef
.Le1c8: mov ax,0xa
.Le1cb: push ax
.Le1cc: push word [bp+0x4]
.Le1cf: push di
.Le1d0: call near ac_call_itoa
.Le1d3: add sp,0x6
.Le1d6: jmp short .Le1ef
.Le1d8: push word [bp+0x4]
.Le1db: push word [bp+0x6]
.Le1de: call near ac_call_manual
.Le1e1: pop bx
.Le1e2: pop bx
.Le1e3: mov_load di,ax
.Le1e5: or_load di,di
.Le1e7: jl .Le1ef
.Le1e9: sub_load ax,ax
.Le1eb: push ax
.Le1ec: call near ac_call_log
.Le1ef: call near ac_call_service_6dca
.Le1f2: or_load di,di
.Le1f4: jnl .Le1fb
.Le1f6: mov ax,0x1
.Le1f9: jmp short .Le1fd
.Le1fb: sub_load ax,ax
.Le1fd: mov [ac_failure],ax
.Le200: mov ax,[bp-0x2]
.Le203: pop di
.Le204: mov_load sp,bp
.Le206: pop bp
.Le207: ret word 0x6
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=8
; 4 0xe20a; 159 original bytes.
aspect_connection_dial_commit:
.Le20a: push bp
.Le20b: mov_load bp,sp
.Le20d: push si
.Le20e: sub_load si,si
.Le210: cmp word [bp+0x4],0xffffffffffffffff
.Le214: jnz .Le219
.Le216: jmp near .Le2a0
.Le219: push word [bp+0x4]
.Le21c: call near ac_call_service_ddb6
.Le21f: pop bx
.Le220: cmp [bp+0x4],si
.Le223: jz .Le248
.Le225: inc word [ac_call_count]
.Le229: call near ac_call_service_36d4
.Le22c: push ax
.Le22d: mov ax,ac_call_date
.Le230: push ax
.Le231: call near ac_call_service_8268
.Le234: pop bx
.Le235: pop bx
.Le236: push word [bp+0x4]
.Le239: call near ac_call_service_dd94
.Le23c: pop bx
.Le23d: sub_load ax,ax
.Le23f: push ax
.Le240: push word [bp+0x4]
.Le243: call near ac_call_service_dd28
.Le246: pop bx
.Le247: pop bx
.Le248: mov al,[ac_record_terminal]
.Le24b: cbw
.Le24c: mov [ac_terminal],ax
.Le24f: mov al,[ac_record_protocol]
.Le252: cbw
.Le253: mov [ac_protocol],ax
.Le256: sub_load ax,ax
.Le258: push ax
.Le259: call near ac_call_log
.Le25c: mov ax,0x1
.Le25f: push ax
.Le260: call near ac_call_service_20a4
.Le263: pop bx
.Le264: cmp byte [ac_record_meta],0x20
.Le269: jz .Le282
.Le26b: cmp byte [ac_record_meta],0x0
.Le270: jz .Le282
.Le272: mov ax,ac_record_meta
.Le275: push ax
.Le276: mov ax,ac_meta_name
.Le279: push ax
.Le27a: call near ac_call_service_8268
.Le27d: pop bx
.Le27e: pop bx
.Le27f: mov si,0x4
.Le282: cmp byte [ac_record_key],0x20
.Le287: jz .Le2a0
.Le289: cmp byte [ac_record_key],0x0
.Le28e: jz .Le2a0
.Le290: mov ax,ac_record_key
.Le293: push ax
.Le294: mov ax,ac_key_name
.Le297: push ax
.Le298: call near ac_call_service_8268
.Le29b: pop bx
.Le29c: pop bx
.Le29d: or si,0x2
.Le2a0: mov_load ax,si
.Le2a2: pop si
.Le2a3: mov_load sp,bp
.Le2a5: pop bp
.Le2a6: ret word 0x2
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=9
; 5 0xe423; 107 original bytes.
aspect_connection_selection_list:
.Le423: push bp
.Le424: mov_load bp,sp
.Le426: sub sp,0x2
.Le429: push di
.Le42a: push word [bp+0x4]
.Le42d: call near ac_call_service_8d18
.Le430: pop bx
.Le431: or_load ax,ax
.Le433: jz .Le486
.Le435: call near ac_call_service_ec49
.Le438: push word [bp+0x4]
.Le43b: call near ac_call_service_9128
.Le43e: pop bx
.Le43f: mov ax,ac_selection_end
.Le442: push ax
.Le443: push word [bp+0x4]
.Le446: call near ac_call_service_97bc
.Le449: pop bx
.Le44a: pop bx
.Le44b: mov_load di,ax
.Le44d: mov word [bp-0x2],ac_selections
.Le452: or_load di,di
.Le454: jz .Le486
.Le456: cmp word [bp-0x2],strict word ac_selection_end
.Le45b: jnc .Le486
.Le45d: mov ax,0x5
.Le460: push ax
.Le461: push di
.Le462: push word [bp-0x2]
.Le465: call near ac_call_service_9888
.Le468: add sp,0x6
.Le46b: mov bx,[bp-0x2]
.Le46e: mov byte [bx+0x6],0x0
.Le472: add word [bp-0x2],0x7
.Le476: mov ax,ac_token_separators
.Le479: push ax
.Le47a: sub_load ax,ax
.Le47c: push ax
.Le47d: call near ac_call_service_97bc
.Le480: pop bx
.Le481: pop bx
.Le482: mov_load di,ax
.Le484: jmp short .Le452
.Le486: call near ac_call_loop
.Le489: pop di
.Le48a: mov_load sp,bp
.Le48c: pop bp
.Le48d: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=10
; 5 0xe556; 141 original bytes.
aspect_connection_manual_record:
.Le556: push bp
.Le557: mov_load bp,sp
.Le559: call near ac_call_service_ec49
.Le55c: mov ax,ac_manual_token
.Le55f: push ax
.Le560: mov ax,ac_selections
.Le563: push ax
.Le564: call near ac_call_service_8268
.Le567: pop bx
.Le568: pop bx
.Le569: mov byte [ac_selection_flags],0x0
.Le56e: mov ax,0x18
.Le571: push ax
.Le572: cmp word [bp+0x6],0x0
.Le576: jnz .Le57d
.Le578: mov ax,ac_manual_name
.Le57b: jmp short .Le580
.Le57d: mov ax,[bp+0x6]
.Le580: push ax
.Le581: mov ax,ac_record
.Le584: push ax
.Le585: call near ac_call_service_9888
.Le588: mov_load sp,bp
.Le58a: push word [bp+0x4]
.Le58d: mov ax,ac_number
.Le590: push ax
.Le591: call near ac_call_service_8268
.Le594: pop bx
.Le595: pop bx
.Le596: mov ax,[ac_baud]
.Le599: mov [ac_data_e67e],ax
.Le59c: mov al,[ac_parity]
.Le59f: mov [ac_data_e680],al
.Le5a2: mov al,[ac_data_bits]
.Le5a5: mov [ac_data_e681],al
.Le5a8: mov al,[ac_stop]
.Le5ab: mov [ac_data_e682],al
.Le5ae: mov al,[ac_port]
.Le5b1: inc al
.Le5b3: mov [ac_data_e6b8],al
.Le5b6: mov al,[ac_duplex]
.Le5b9: mov [ac_data_e683],al
.Le5bc: mov word [ac_call_count],0x0
.Le5c2: sub_load al,al
.Le5c4: mov [ac_data_e684],al
.Le5c7: mov [ac_call_date],al
.Le5ca: mov [ac_record_meta],al
.Le5cd: mov [ac_record_key],al
.Le5d0: mov [ac_record_protocol],al
.Le5d3: mov [ac_data_e69a],al
.Le5d6: mov al,[ac_terminal]
.Le5d9: mov [ac_record_terminal],al
.Le5dc: call near ac_call_loop
.Le5df: mov_load sp,bp
.Le5e1: pop bp
.Le5e2: ret
%endif

%if ASPECT_CONNECTION_UNIT=0 || ASPECT_CONNECTION_UNIT=11
; 5 0xe5e3; 714 original bytes.
aspect_connection_dial_loop:
.Le5e3: push bp
.Le5e4: mov_load bp,sp
.Le5e6: sub sp,0x50
.Le5e9: push si
.Le5ea: call near ac_call_service_aa5c
.Le5ed: or_load ax,ax
.Le5ef: jz .Le5f4
.Le5f1: call near ac_call_service_ec0e
.Le5f4: sub_load dx,dx
.Le5f6: mov bx,ac_selection_flags
.Le5f9: jmp short .Le604
.Le5fb: cmp byte [bx],0x0
.Le5fe: jnz .Le601
.Le600: inc dx
.Le601: add bx,0x7
.Le604: cmp bx,strict word ac_selection_flag_end
.Le608: jc .Le5fb
.Le60a: or_load dx,dx
.Le60c: jnz .Le611
.Le60e: jmp near .Le8a5
.Le611: mov [bp-0x8],dx
.Le614: mov ax,ac_data_6ff2
.Le617: push ax
.Le618: call near ac_call_service_3fc7
.Le61b: pop bx
.Le61c: mov [bp-0x12],ax
.Le61f: mov [bp-0x10],dx
.Le622: push word [ac_data_e6c2]
.Le626: push word [ac_data_e6c4]
.Le62a: push word [ac_data_1f7a]
.Le62e: call near ac_call_service_4056
.Le631: mov ax,ac_data_68b2
.Le634: push ax
.Le635: call near ac_call_service_780e
.Le638: mov word [bp-0xe],0x1
.Le63d: mov word [bp-0x6],0xffff
.Le642: push word [ac_data_e6c6]
.Le646: push word [ac_data_1f7a]
.Le64a: sub_load ax,ax
.Le64c: push ax
.Le64d: call near ac_call_service_498b
.Le650: pop bx
.Le651: push ax
.Le652: call near ac_call_service_6bf0
.Le655: cmp word [bp-0x8],0x0
.Le659: jnz .Le65e
.Le65b: jmp near .Le87a
.Le65e: inc word [bp-0x6]
.Le661: cmp word [bp-0x6],0xf
.Le665: jnz .Le67a
.Le667: mov ax,[ac_cycle_limit]
.Le66a: inc word [bp-0xe]
.Le66d: cmp [bp-0xe],ax
.Le670: jng .Le675
.Le672: jmp near .Le892
.Le675: mov word [bp-0x6],0x0
.Le67a: mov ax,0x7
.Le67d: imul word [bp-0x6]
.Le680: mov_load bx,ax
.Le682: cmp byte [bx+ac_selection_flags],0x0
.Le687: jnz .Le655
.Le689: lea ax,[bp-0x50]
.Le68c: push ax
.Le68d: push word [bp-0x6]
.Le690: call near ac_call_service_ec61
.Le693: pop bx
.Le694: pop bx
.Le695: mov_load si,ax
.Le697: or_load si,si
.Le699: jl .Le6a1
.Le69b: cmp si,strict word 0xc8
.Le69f: jng .Le6a4
.Le6a1: jmp near .Le836
.Le6a4: cmp word [ac_script_stream],0x0
.Le6a9: jnz .Le6da
.Le6ab: or_load si,si
.Le6ad: jz .Le6da
.Le6af: lea ax,[si-0x1]
.Le6b2: cwd
.Le6b3: idiv word [ac_data_6f4a]
.Le6b7: inc ax
.Le6b8: mov [bp-0x4],ax
.Le6bb: mov_load ax,si
.Le6bd: cwd
.Le6be: idiv word [ac_data_6f4a]
.Le6c2: mov [bp-0x2],dx
.Le6c5: or_load dx,dx
.Le6c7: jnz .Le6cf
.Le6c9: mov ax,[ac_data_6f4a]
.Le6cc: mov [bp-0x2],ax
.Le6cf: push word [bp-0x2]
.Le6d2: push word [bp-0x4]
.Le6d5: call near ac_call_service_da4e
.Le6d8: pop bx
.Le6d9: pop bx
.Le6da: or_load si,si
.Le6dc: jz .Le6e3
.Le6de: push si
.Le6df: call near ac_call_service_ddb6
.Le6e2: pop bx
.Le6e3: sub_load ax,ax
.Le6e5: push ax
.Le6e6: call near ac_call_service_eaed
.Le6e9: pop bx
.Le6ea: cmp byte [ac_data_e6b8],0x0
.Le6ef: jz .Le707
.Le6f1: mov al,[ac_data_e6b8]
.Le6f4: cbw
.Le6f5: sub ax,[ac_port]
.Le6f9: dec ax
.Le6fa: jz .Le707
.Le6fc: call near ac_call_service_adba
.Le6ff: mov al,[ac_data_e6b8]
.Le702: cbw
.Le703: dec ax
.Le704: mov [ac_port],ax
.Le707: mov ax,[ac_data_e67e]
.Le70a: mov [ac_baud],ax
.Le70d: mov al,[ac_data_e680]
.Le710: cbw
.Le711: mov [ac_parity],ax
.Le714: mov al,[ac_data_e682]
.Le717: cbw
.Le718: mov [ac_stop],ax
.Le71b: mov al,[ac_data_e681]
.Le71e: cbw
.Le71f: mov [ac_data_bits],ax
.Le722: mov al,[ac_data_e683]
.Le725: cbw
.Le726: mov [ac_duplex],ax
.Le729: call near ac_call_service_03a7
.Le72c: mov ax,ac_record
.Le72f: push ax
.Le730: mov ax,ac_data_667c
.Le733: push ax
.Le734: push word [ac_data_1f7a]
.Le738: push word [ac_data_e6c8]
.Le73c: call near ac_call_service_75e8
.Le73f: add sp,0x8
.Le742: mov ax,ac_call_date
.Le745: push ax
.Le746: mov ax,ac_data_664c
.Le749: push ax
.Le74a: push word [ac_data_1f7a]
.Le74e: push word [ac_data_e6ca]
.Le752: call near ac_call_service_75e8
.Le755: add sp,0x8
.Le758: mov ax,ac_number
.Le75b: push ax
.Le75c: mov ax,ac_data_6672
.Le75f: push ax
.Le760: push word [ac_data_1f7a]
.Le764: push word [ac_data_e6cc]
.Le768: call near ac_call_service_75e8
.Le76b: add sp,0x8
.Le76e: push word [ac_call_count]
.Le772: mov ax,ac_data_6626
.Le775: push ax
.Le776: push word [ac_data_1f7a]
.Le77a: push word [ac_data_e6ce]
.Le77e: call near ac_call_service_75e8
.Le781: add sp,0x8
.Le784: mov ax,ac_data_e684
.Le787: push ax
.Le788: mov ax,ac_data_664c
.Le78b: push ax
.Le78c: push word [ac_data_1f7a]
.Le790: push word [ac_data_e6d0]
.Le794: call near ac_call_service_75e8
.Le797: add sp,0x8
.Le79a: push word [ac_data_1b8e]
.Le79e: mov ax,ac_data_6626
.Le7a1: push ax
.Le7a2: push word [ac_data_1f7a]
.Le7a6: push word [ac_data_e464]
.Le7aa: call near ac_call_service_75e8
.Le7ad: add sp,0x8
.Le7b0: push word [ac_data_1b90]
.Le7b4: mov ax,ac_data_6626
.Le7b7: push ax
.Le7b8: push word [ac_data_1f7a]
.Le7bc: push word [ac_data_e466]
.Le7c0: call near ac_call_service_75e8
.Le7c3: add sp,0x8
.Le7c6: call near ac_call_service_2fb8
.Le7c9: push word [bp-0xe]
.Le7cc: mov ax,ac_data_6626
.Le7cf: push ax
.Le7d0: push word [ac_data_1f7a]
.Le7d4: push word [ac_data_e468]
.Le7d8: call near ac_call_service_75e8
.Le7db: add sp,0x8
.Le7de: cmp byte [ac_data_e69a],0x0
.Le7e3: jnz .Le7ef
.Le7e5: lea ax,[bp-0x50]
.Le7e8: push ax
.Le7e9: call near ac_call_attempt
.Le7ec: pop bx
.Le7ed: jmp short .Le7f2
.Le7ef: mov ax,0x1
.Le7f2: mov [bp-0x2],ax
.Le7f5: cmp ax,strict word 0x1b
.Le7f8: jnz .Le7fd
.Le7fa: jmp near .Le892
.Le7fd: ja .Le807
.Le7ff: dec al
.Le801: jz .Le849
.Le803: sub al,0x2
.Le805: jz .Le814
.Le807: call near ac_call_service_eb89
.Le80a: cmp ax,strict word 0x1b
.Le80d: jz .Le812
.Le80f: jmp near .Le655
.Le812: jmp short .Le892
.Le814: cmp byte [si+ac_data_e57e],0x0
.Le819: jz .Le824
.Le81b: mov byte [si+ac_data_e57e],0x0
.Le820: dec word [ac_data_6f50]
.Le824: mov ax,0x7
.Le827: imul word [bp-0x6]
.Le82a: mov_load bx,ax
.Le82c: mov byte [bx+ac_selection_flags],0x1
.Le831: dec word [bp-0x8]
.Le834: jmp short .Le807
.Le836: mov ax,0x7
.Le839: imul word [bp-0x6]
.Le83c: mov_load bx,ax
.Le83e: mov byte [bx+ac_selection_flags],0x1
.Le843: dec word [bp-0x8]
.Le846: jmp near .Le655
.Le849: mov ax,0x7
.Le84c: imul word [bp-0x6]
.Le84f: mov_load bx,ax
.Le851: mov byte [bx+ac_selection_flags],0x1
.Le856: push word [bp-0x10]
.Le859: push word [bp-0x12]
.Le85c: mov ax,ac_data_6ff2
.Le85f: push ax
.Le860: call near ac_call_service_4015
.Le863: add sp,0x6
.Le866: cmp byte [si+ac_data_e57e],0x0
.Le86b: jz .Le876
.Le86d: mov byte [si+ac_data_e57e],0x0
.Le872: dec word [ac_data_6f50]
.Le876: mov_load ax,si
.Le878: jmp short .Le8a8
.Le87a: mov ax,ac_data_69f0
.Le87d: push ax
.Le87e: mov ax,ac_data_6686
.Le881: push ax
.Le882: mov ax,[ac_data_1f7a]
.Le885: or al,0x80
.Le887: push ax
.Le888: push word [ac_data_e46a]
.Le88c: call near ac_call_service_75e8
.Le88f: add sp,0x8
.Le892: push word [bp-0x10]
.Le895: push word [bp-0x12]
.Le898: mov ax,ac_data_6ff2
.Le89b: push ax
.Le89c: call near ac_call_service_4015
.Le89f: add sp,0x6
.Le8a2: call near ac_call_service_abca
.Le8a5: mov ax,0xffff
.Le8a8: pop si
.Le8a9: mov_load sp,bp
.Le8ab: pop bp
.Le8ac: ret
%endif
