; Recovered CSI dispatcher, overlay 12, including two typed jump tables.
; REA Evidence ev_5054c5700c911ddb639380e599bef490251714e34d8e56b6b3cc7c11b9667ba4.
BITS 16
CPU 8086
%ifdef ANSI_OMF
SEGMENT _TEXT public class=CODE use16
global ansi_dispatch_command
%define short
%else
ORG 0xe4b2
%endif
%include "encodings.inc"
%include "dispatch-layout.inc"
ansi_dispatch_command:
L_e4b2: push bp
L_e4b3: mov_load bp,sp
L_e4b5: sub sp,0x2
L_e4b8: push di
L_e4b9: push si
L_e4ba: mov di,[ansi_command]
L_e4be: mov_load ax,di
L_e4c0: jmp near L_ebc4
L_e4c3: nop
L_e4c4: mov word [csi_wrap_pending],0x0
L_e4ca: cmp word [ansi_parameters],0x1
L_e4cf: jnl short L_e4d7
L_e4d1: mov word [ansi_parameters],0x1
L_e4d7: cmp word [(ansi_parameters+2)],0x1
L_e4dc: jnl short L_e4e4
L_e4de: mov word [(ansi_parameters+2)],0x1
L_e4e4: mov ax,[csi_origin_row]
L_e4e7: add ax,[ansi_parameters]
L_e4eb: cmp ax,[csi_row_count]
L_e4ef: jng short L_e4fb
L_e4f1: mov ax,[csi_row_count]
L_e4f4: sub ax,[csi_origin_row]
L_e4f8: mov [ansi_parameters],ax
L_e4fb: mov ax,[(ansi_parameters+2)]
L_e4fe: cmp [csi_column_count],ax
L_e502: jnc short L_e50a
L_e504: mov ax,[csi_column_count]
L_e507: mov [(ansi_parameters+2)],ax
L_e50a: cmp word [ansi_parameter_count],0x2
L_e50f: jnz short L_e522
L_e511: mov ax,[csi_origin_row]
L_e514: add ax,[ansi_parameters]
L_e518: dec ax
L_e519: mov dx,[(ansi_parameters+2)]
L_e51d: dec dx
L_e51e: jmp near L_e9cb
L_e521: nop
L_e522: cmp word [ansi_parameter_count],0x1
L_e527: jz short L_e52c
L_e529: jmp near L_e9c6
L_e52c: mov ax,[csi_origin_row]
L_e52f: add ax,[ansi_parameters]
L_e533: dec ax
L_e534: jmp near L_e9c9
L_e537: nop
L_e538: mov word [csi_wrap_pending],0x0
L_e53e: mov si,0x1
L_e541: jmp short L_e548
L_e543: nop
L_e544: call screen_cursor_up
L_e547: inc si
L_e548: cmp [ansi_parameters],si
L_e54c: jg short L_e544
L_e54e: call screen_cursor_up
L_e551: jmp near L_e9ce
L_e554: mov word [csi_wrap_pending],0x0
L_e55a: mov si,0x1
L_e55d: jmp short L_e564
L_e55f: nop
L_e560: call screen_cursor_down
L_e563: inc si
L_e564: cmp [ansi_parameters],si
L_e568: jg short L_e560
L_e56a: call screen_cursor_down
L_e56d: jmp near L_e9ce
L_e570: mov word [csi_wrap_pending],0x0
L_e576: mov si,0x1
L_e579: jmp short L_e580
L_e57b: nop
L_e57c: call screen_cursor_right
L_e57f: inc si
L_e580: cmp [ansi_parameters],si
L_e584: jg short L_e57c
L_e586: call screen_cursor_right
L_e589: jmp near L_e9ce
L_e58c: mov si,0x1
L_e58f: jmp short L_e596
L_e591: nop
L_e592: call screen_cursor_left
L_e595: inc si
L_e596: cmp [ansi_parameters],si
L_e59a: jg short L_e592
L_e59c: call screen_cursor_left
L_e59f: jmp near L_e9ce
L_e5a2: cmp word [ansi_parameter_count],0x0
L_e5a7: jnz short L_e5b0
L_e5a9: call attributes_normal
L_e5ac: jmp near L_e9ce
L_e5af: nop
L_e5b0: sub_load si,si
L_e5b2: jmp near L_e77d
L_e5b5: nop
L_e5b6: call attributes_normal
L_e5b9: jmp near L_e77c
L_e5bc: call attributes_bold
L_e5bf: jmp near L_e77c
L_e5c2: call attributes_underline
L_e5c5: jmp near L_e77c
L_e5c8: call attributes_blink
L_e5cb: jmp near L_e77c
L_e5ce: call attributes_reverse
L_e5d1: jmp near L_e77c
L_e5d4: call attributes_default_transform
L_e5d7: jmp near L_e77c
L_e5da: mov word [attributes_bold_active],0x0
L_e5e0: and word [attributes_current],0xf7
L_e5e6: jmp near L_e77c
L_e5e9: nop
L_e5ea: mov ax,[attributes_normal_value]
L_e5ed: mov [attributes_current],ax
L_e5f0: cmp word [attributes_blink_active],0x0
L_e5f5: jz short L_e5fc
L_e5f7: or al,0x80
L_e5f9: mov [attributes_current],ax
L_e5fc: cmp word [attributes_bold_active],0x0
L_e601: jnz short L_e606
L_e603: jmp near L_e77c
L_e606: or byte [attributes_current],0x8
L_e60b: jmp near L_e77c
L_e60e: mov word [attributes_blink_active],0x0
L_e614: and word [attributes_current],0x7f
L_e619: jmp near L_e77c
L_e61c: cmp byte [attributes_reverse_active],0x0
L_e621: jnz short L_e626
L_e623: jmp near L_e77c
L_e626: mov byte [attributes_reverse_active],0x0
L_e62b: call attributes_reverse
L_e62e: mov byte [attributes_reverse_active],0x0
L_e633: jmp near L_e77c
L_e636: and word [attributes_current],0xf8
L_e63c: jmp near L_e77c
L_e63f: nop
L_e640: and word [attributes_current],0xf8
L_e646: or byte [attributes_current],0x4
L_e64b: jmp near L_e77c
L_e64e: and word [attributes_current],0xf8
L_e654: or byte [attributes_current],0x2
L_e659: jmp near L_e77c
L_e65c: and word [attributes_current],0xf8
L_e662: or byte [attributes_current],0x6
L_e667: jmp near L_e77c
L_e66a: and word [attributes_current],0xf8
L_e670: or byte [attributes_current],0x1
L_e675: jmp near L_e77c
L_e678: and word [attributes_current],0xf8
L_e67e: or byte [attributes_current],0x5
L_e683: jmp near L_e77c
L_e686: and word [attributes_current],0xf8
L_e68c: or byte [attributes_current],0x3
L_e691: jmp near L_e77c
L_e694: and word [attributes_current],0xf8
L_e69a: or byte [attributes_current],0x7
L_e69f: jmp near L_e77c
L_e6a2: and word [attributes_current],0x8f
L_e6a8: jmp near L_e77c
L_e6ab: nop
L_e6ac: and word [attributes_current],0x8f
L_e6b2: or byte [attributes_current],0x40
L_e6b7: jmp near L_e77c
L_e6ba: and word [attributes_current],0x8f
L_e6c0: or byte [attributes_current],0x20
L_e6c5: jmp near L_e77c
L_e6c8: and word [attributes_current],0x8f
L_e6ce: or byte [attributes_current],0x60
L_e6d3: jmp near L_e77c
L_e6d6: and word [attributes_current],0x8f
L_e6dc: or byte [attributes_current],0x10
L_e6e1: jmp near L_e77c
L_e6e4: and word [attributes_current],0x8f
L_e6ea: or byte [attributes_current],0x50
L_e6ef: jmp near L_e77c
L_e6f2: and word [attributes_current],0x8f
L_e6f8: or byte [attributes_current],0x30
L_e6fd: jmp short L_e77c
L_e6ff: nop
L_e700: and word [attributes_current],0x8f
L_e706: or byte [attributes_current],0x70
L_e70b: jmp short L_e77c
L_e70d: nop
L_e70e: cmp ax,strict word 0x2f
L_e711: ja short L_e77c
L_e713: shl ax,1
L_e715: xchg ax,bx
L_e716: jmp word near [cs:bx+csi_sgr_table]
L_e71b: nop
csi_sgr_table:
 dw L_e5b6
 dw L_e5bc
 dw L_e77c
 dw L_e77c
 dw L_e5c2
 dw L_e5c8
 dw L_e77c
 dw L_e5ce
 dw L_e5d4
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e77c
 dw L_e5da
 dw L_e77c
 dw L_e5ea
 dw L_e60e
 dw L_e77c
 dw L_e61c
 dw L_e77c
 dw L_e77c
 dw L_e636
 dw L_e640
 dw L_e64e
 dw L_e65c
 dw L_e66a
 dw L_e678
 dw L_e686
 dw L_e694
 dw L_e77c
 dw L_e77c
 dw L_e6a2
 dw L_e6ac
 dw L_e6ba
 dw L_e6c8
 dw L_e6d6
 dw L_e6e4
 dw L_e6f2
 dw L_e700
L_e77c: inc si
L_e77d: cmp [ansi_parameter_count],si
L_e781: jng short L_e78e
L_e783: mov_load bx,si
L_e785: shl bx,1
L_e787: mov ax,[bx+ansi_parameters]
L_e78b: jmp short L_e70e
L_e78d: nop
L_e78e: cmp word [attributes_bold_active],0x0
L_e793: jz short L_e79a
L_e795: or byte [attributes_current],0x8
L_e79a: cmp word [attributes_blink_active],0x0
L_e79f: jnz short L_e7a4
L_e7a1: jmp near L_e9ce
L_e7a4: or byte [attributes_current],0x80
L_e7a9: jmp near L_e9ce
L_e7ac: mov word [csi_wrap_pending],0x0
L_e7b2: cmp word [ansi_parameter_count],0x0
L_e7b7: jnz short L_e7be
L_e7b9: mov ax,0x1
L_e7bc: jmp short L_e818
L_e7be: cmp word [ansi_parameters],0x0
L_e7c3: jz short L_e7b9
L_e7c5: cmp word [ansi_parameters],0x1
L_e7ca: jnz short L_e7d2
L_e7cc: call csi_service_d85e
L_e7cf: jmp near L_e9ce
L_e7d2: cmp word [ansi_parameters],0x2
L_e7d7: jz short L_e7dc
L_e7d9: jmp near L_e9ce
L_e7dc: cmp word [attributes_monochrome],0x0
L_e7e1: jz short L_e7ea
L_e7e3: call csi_service_da12
L_e7e6: jmp near L_e9ce
L_e7e9: nop
L_e7ea: sub_load ax,ax
L_e7ec: push ax
L_e7ed: push ax
L_e7ee: mov al,[csi_last_column]
L_e7f1: mov ah,[csi_last_row]
L_e7f5: push ax
L_e7f6: mov al,[csi_erase_attribute]
L_e7f9: sub_load ah,ah
L_e7fb: push ax
L_e7fc: call csi_service_2530
L_e7ff: jmp near L_e9ce
L_e802: mov word [csi_wrap_pending],0x0
L_e808: cmp word [ansi_parameter_count],0x0
L_e80d: jz short L_e816
L_e80f: cmp word [ansi_parameters],0x0
L_e814: jnz short L_e820
L_e816: sub_load ax,ax
L_e818: push ax
L_e819: call csi_service_d8b6
L_e81c: jmp near L_e9ce
L_e81f: nop
L_e820: cmp word [ansi_parameters],0x1
L_e825: jnz short L_e82e
L_e827: call csi_service_d844
L_e82a: jmp near L_e9ce
L_e82d: nop
L_e82e: cmp word [ansi_parameters],0x2
L_e833: jz short L_e838
L_e835: jmp near L_e9ce
L_e838: mov si,[screen_cursor_column]
L_e83c: mov word [screen_cursor_column],0x0
L_e842: sub_load ax,ax
L_e844: push ax
L_e845: call csi_service_d8b6
L_e848: mov [screen_cursor_column],si
L_e84c: jmp near L_e9ce
L_e84f: nop
L_e850:
%ifdef ANSI_OMF
 ; Maintained ECH: default zero/omitted count to one, then bound the
 ; rectangle to the remaining row. Original arithmetic can invert the
 ; rectangle or carry the column into its packed row byte.
 mov cx,[csi_last_column]
 cmp [screen_cursor_column],cx
 ja ansi_x_ignore_invalid_column
 inc cx
 sub cx,[screen_cursor_column]
 mov ax,[ansi_parameters]
 cmp ax,1
 jae ansi_x_positive_count
 mov ax,1
ansi_x_positive_count:
 cmp ax,cx
 jbe ansi_x_count_fits
 mov ax,cx
ansi_x_count_fits:
 mov [ansi_parameters],ax
 jmp ansi_x_count_ready
ansi_x_ignore_invalid_column:
 jmp L_e9ce
ansi_x_count_ready:
%endif
 mov ax,[screen_cursor_column]
L_e853: add ax,[ansi_parameters]
L_e857: dec ax
L_e858: mov_load si,ax
L_e85a: sub_load cx,cx
L_e85c: mov [csi_wrap_pending],cx
L_e860: push cx
L_e861: mov ch,[screen_cursor_row]
L_e865: sub_load cl,cl
L_e867: mov_load dx,cx
L_e869: or cx,[screen_cursor_column]
L_e86d: push cx
L_e86e: or_load dx,ax
L_e870: push dx
L_e871: push word [attributes_current]
L_e875: jmp short L_e7fc
L_e877: nop
L_e878: mov word [csi_wrap_pending],0x0
L_e87e: mov si,0x1
L_e881: jmp short L_e888
L_e883: nop
L_e884: call csi_service_d440
L_e887: inc si
L_e888: cmp [ansi_parameters],si
L_e88c: jg short L_e884
L_e88e: call csi_service_d440
L_e891: jmp near L_e9ce
L_e894: mov word [csi_wrap_pending],0x0
L_e89a: mov si,0x1
L_e89d: jmp short L_e8a4
L_e89f: nop
L_e8a0: call csi_service_d270
L_e8a3: inc si
L_e8a4: cmp [ansi_parameters],si
L_e8a8: jg short L_e8a0
L_e8aa: call csi_service_d270
L_e8ad: jmp near L_e9ce
L_e8b0: mov si,0x1
L_e8b3: jmp short L_e8ba
L_e8b5: nop
L_e8b6: call csi_service_d668
L_e8b9: inc si
L_e8ba: cmp [ansi_parameters],si
L_e8be: jg short L_e8b6
L_e8c0: call csi_service_d668
L_e8c3: jmp near L_e9ce
L_e8c6: cmp word [attributes_monochrome],0x0
L_e8cb: jz short L_e8d4
L_e8cd: call csi_service_daf2
L_e8d0: jmp near L_e9ce
L_e8d3: nop
L_e8d4: mov si,0x1
L_e8d7: jmp short L_e8de
L_e8d9: nop
L_e8da: call csi_service_d73c
L_e8dd: inc si
L_e8de: cmp [ansi_parameters],si
L_e8e2: jg short L_e8da
L_e8e4: call csi_service_d73c
L_e8e7: jmp near L_e9ce
L_e8ea: mov si,0x1
L_e8ed: jmp short L_e8f4
L_e8ef: nop
L_e8f0: call csi_service_12c8
L_e8f3: inc si
L_e8f4: cmp [ansi_parameters],si
L_e8f8: jg short L_e8f0
L_e8fa: call csi_service_12c8
L_e8fd: jmp near L_e9ce
L_e900: mov word [screen_cursor_column],0x0
L_e906: mov si,0x1
L_e909: jmp short L_e910
L_e90b: nop
L_e90c: call csi_service_da84
L_e90f: inc si
L_e910: cmp [ansi_parameters],si
L_e914: jg short L_e90c
L_e916: call csi_service_da84
L_e919: jmp near L_e9ce
L_e91c: cmp word [ansi_parameters],0x1
L_e921: jg short L_e928
L_e923: sub_load si,si
L_e925: jmp short L_e93b
L_e927: nop
L_e928: mov ax,[ansi_parameters]
L_e92b: cmp [csi_column_count],ax
L_e92f: ja short L_e938
L_e931: mov si,[csi_last_column]
L_e935: jmp short L_e93b
L_e937: nop
L_e938: mov_load si,ax
L_e93a: dec si
L_e93b: mov ax,[screen_cursor_row]
L_e93e: mov_load dx,si
L_e940: jmp near L_e9cb
L_e943: nop
L_e944: call csi_set_modes
L_e947: jmp near L_e9ce
L_e94a: nop
L_e94b: nop
L_e94c: call csi_reset_modes
L_e94f: jmp short L_e9ce
L_e951: nop
L_e952: cmp word [ansi_parameters],0x1
L_e957: jnl short L_e95f
L_e959: mov word [ansi_parameters],0x1
L_e95f: cmp word [(ansi_parameters+2)],0x1
L_e964: jnl short L_e96c
L_e966: mov ax,[csi_row_count]
L_e969: mov [(ansi_parameters+2)],ax
L_e96c: mov ax,[csi_row_count]
L_e96f: cmp [(ansi_parameters+2)],ax
L_e973: jng short L_e978
L_e975: mov [(ansi_parameters+2)],ax
L_e978: cmp word [ansi_parameter_count],0x2
L_e97d: jnz short L_e990
L_e97f: mov ax,[ansi_parameters]
L_e982: dec ax
L_e983: mov [csi_scroll_top],ax
L_e986: mov ax,[(ansi_parameters+2)]
L_e989: dec ax
L_e98a: mov [csi_scroll_bottom],ax
L_e98d: jmp short L_e9a7
L_e98f: nop
L_e990: cmp word [ansi_parameter_count],0x1
L_e995: jnz short L_e9a4
L_e997: mov ax,[ansi_parameters]
L_e99a: dec ax
L_e99b: mov [csi_scroll_top],ax
L_e99e: mov ax,[csi_last_row]
L_e9a1: jmp short L_e98a
L_e9a3: nop
L_e9a4: call csi_reset_scroll_region
L_e9a7: mov ax,[csi_scroll_top]
L_e9aa: cmp [csi_scroll_bottom],ax
L_e9ae: jg short L_e9b3
L_e9b0: call csi_reset_scroll_region
L_e9b3: cmp word [csi_origin_mode],0x0
L_e9b8: jz short L_e9c6
L_e9ba: mov ax,[csi_scroll_top]
L_e9bd: mov [csi_origin_row],ax
L_e9c0: mov ax,[csi_scroll_bottom]
L_e9c3: mov [csi_origin_bottom],ax
L_e9c6: mov ax,[csi_origin_row]
L_e9c9: sub_load dx,dx
L_e9cb: call screen_set_cursor
L_e9ce: mov ax,0x52
L_e9d1: pop si
L_e9d2: pop di
L_e9d3: mov_load sp,bp
L_e9d5: pop bp
L_e9d6: ret
L_e9d7: nop
L_e9d8: call csi_media_copy
L_e9db: jmp short L_e9ce
L_e9dd: nop
L_e9de: cmp word [ansi_secondary],0x0
L_e9e3: jz short L_ea20
L_e9e5: mov ax,csi_secondary_prefix
L_e9e8: push ax
L_e9e9: call csi_transmit_string
L_e9ec: mov ax,[csi_terminal_id]
L_e9ef: sub ax,strict word 0x4
L_e9f2: jz short L_ea00
L_e9f4: dec ax
L_e9f5: jz short L_ea10
L_e9f7: sub ax,strict word 0x4
L_e9fa: jz short L_ea16
L_e9fc: dec ax
L_e9fd: dec ax
L_e9fe: jnz short L_ea07
L_ea00: mov ax,csi_secondary_322c
L_ea03: push ax
L_ea04: call csi_transmit_string
L_ea07: mov ax,0x63
L_ea0a: push ax
L_ea0b: call csi_transmit_byte
L_ea0e: jmp short L_e9ce
L_ea10: mov ax,csi_secondary_7529
L_ea13: jmp short L_ea03
L_ea15: nop
L_ea16: mov ax,0x34
L_ea19: push ax
L_ea1a: call csi_transmit_byte
L_ea1d: jmp short L_ea07
L_ea1f: nop
L_ea20: cmp word [ansi_private],0x0
L_ea25: jnz short L_e9ce
L_ea27: call csi_primary_attributes
L_ea2a: jmp short L_e9ce
L_ea2c: call csi_device_status
L_ea2f: jmp short L_e9ce
L_ea31: nop
L_ea32: mov ax,0x1
L_ea35: push ax
L_ea36: call csi_save_cursor
L_ea39: jmp short L_ea67
L_ea3b: nop
L_ea3c: mov ax,0x1
L_ea3f: push ax
L_ea40: call csi_restore_cursor
L_ea43: jmp short L_ea67
L_ea45: nop
L_ea46: mov ax,0xffb1
L_ea49: push ax
L_ea4a: call ansi_control_character
L_ea4d: add sp,0x2
L_ea50: mov ax,0x41
L_ea53: pop si
L_ea54: pop di
L_ea55: mov_load sp,bp
L_ea57: pop bp
L_ea58: ret
L_ea59: nop
L_ea5a: cmp word [ansi_parameter_count],0x0
L_ea5f: jnz short L_ea6e
L_ea61: sub_load ax,ax
L_ea63: push ax
L_ea64: call csi_clear_tabs
L_ea67: add sp,0x2
L_ea6a: jmp near L_e9ce
L_ea6d: nop
L_ea6e: cmp word [ansi_parameters],0x0
L_ea73: jnz short L_ea7e
L_ea75: sub_load ax,ax
L_ea77: push ax
L_ea78: call csi_clear_tabs
L_ea7b: add sp,0x2
L_ea7e: cmp word [ansi_parameters],0x3
L_ea83: jz short L_ea88
L_ea85: jmp near L_e9ce
L_ea88: mov ax,0x2
L_ea8b: jmp short L_ea63
L_ea8d: nop
L_ea8e: cmp word [ansi_parameter_count],0x2
%ifdef ANSI_OMF
L_ea93: jmp L_e9ce ; Maintained mode selects the historical TECH_NET behavior.
%else
L_ea93: jnl short L_ea98
%endif
L_ea95: jmp near L_e9ce
L_ea98: mov si,[(ansi_parameters+2)]
L_ea9c: add si,0x10
L_ea9f: jmp short L_eaa6
L_eaa1: nop
L_eaa2: call ansi_next_byte
L_eaa5: dec si
L_eaa6: or_load si,si
L_eaa8: jnz short L_eaa2
L_eaaa: jmp near L_e9ce
L_eaad: nop
L_eaae: call ansi_next_byte
L_eab1: mov_load si,ax
L_eab3: sub ax,strict word 0x70
L_eab6: jnz short L_eb05
L_eab8: mov ax,[ansi_parameters]
L_eabb: sub ax,strict word 0x3d
L_eabe: jz short L_eacc
L_eac0: dec ax
L_eac1: jnl short L_eac6
L_eac3: jmp near L_ebbd
L_eac6: dec ax
L_eac7: jng short L_eae2
L_eac9: jmp near L_ebbd
L_eacc: mov ax,[csi_terminal_id]
L_eacf: mov [csi_previous_terminal_id],ax
L_ead2: mov word [csi_terminal_id],0x2
L_ead8: mov ax,0x1
L_eadb: push ax
L_eadc: call csi_reset_terminal
L_eadf: jmp short L_ea67
L_eae1: nop
L_eae2: cmp word [csi_previous_terminal_id],0x2
L_eae7: jnz short L_eaec
L_eae9: jmp near L_e9ce
L_eaec: mov ax,[csi_previous_terminal_id]
L_eaef: mov [csi_terminal_id],ax
L_eaf2: mov word [csi_previous_terminal_id],0x2
L_eaf8: jmp short L_ead8
L_eafa: call ansi_next_byte
L_eafd: mov [ansi_command],ax
L_eb00: sub ax,strict word 0x7d
L_eb03: jz short L_eb0a
L_eb05: dec ax
L_eb06: jmp near L_ebb8
L_eb09: nop
L_eb0a: cmp word [ansi_parameters],0x1
L_eb0f: jz short L_eb14
L_eb11: jmp near L_e9ce
L_eb14: mov word [bp-0x2],0x0
L_eb19: cmp word [bp-0x2],0x5
L_eb1d: jnz short L_eb22
L_eb1f: jmp near L_e9ce
L_eb22: call ansi_next_byte
L_eb25: mov_load si,ax
L_eb27: cmp si,0xffffffffffffffff
L_eb2a: jnz short L_eb2f
L_eb2c: jmp near L_e9ce
L_eb2f: cmp ax,strict word 0x30
L_eb32: jz short L_eb62
L_eb34: jg short L_eb90
L_eb36: sub ax,strict word 0x1b
L_eb39: jz short L_eb42
L_eb3b: sub ax,strict word 0x9
L_eb3e: jz short L_eb76
L_eb40: jmp short L_eb14
L_eb42: cmp word [bp-0x2],0x0
L_eb46: jnz short L_eb19
L_eb48: inc word [bp-0x2]
L_eb4b: jmp short L_eb19
L_eb4d: nop
L_eb4e: cmp word [bp-0x2],0x1
L_eb52: jmp short L_eb46
L_eb54: cmp word [bp-0x2],0x0
L_eb58: jnz short L_eb19
L_eb5a: mov word [bp-0x2],0x2
L_eb5f: jmp short L_eb19
L_eb61: nop
L_eb62: cmp word [bp-0x2],0x2
L_eb66: jz short L_eb6e
L_eb68: cmp word [bp-0x2],0x3
L_eb6c: jnz short L_eb19
L_eb6e: mov word [bp-0x2],0x3
L_eb73: jmp short L_eb19
L_eb75: nop
L_eb76: cmp word [bp-0x2],0x2
L_eb7a: jz short L_eb82
L_eb7c: cmp word [bp-0x2],0x3
L_eb80: jnz short L_eb19
L_eb82: mov word [bp-0x2],0x4
L_eb87: jmp short L_eb19
L_eb89: nop
L_eb8a: cmp word [bp-0x2],0x4
L_eb8e: jmp short L_eb46
L_eb90: sub ax,strict word 0x5b
L_eb93: jz short L_eb4e
L_eb95: sub ax,strict word 0x22
L_eb98: jz short L_eb8a
L_eb9a: sub ax,strict word 0x1e
L_eb9d: jz short L_eb54
L_eb9f: jmp near L_eb14
L_eba2: call ansi_unread_byte
L_eba5: jmp near L_ea50
L_eba8: call ansi_next_byte
L_ebab: mov_load si,ax
L_ebad: cmp si,0x7a
L_ebb0: jnz short L_ebb5
L_ebb2: jmp near L_e9ce
L_ebb5: cmp si,0x7b
L_ebb8: jnz short L_ebbd
L_ebba: jmp near L_e9ce
L_ebbd: call ansi_unread_byte
L_ebc0: jmp near L_e9ce
L_ebc3: nop
L_ebc4: sub ax,strict word 0x18
L_ebc7: cmp ax,strict word 0x5d
L_ebca: jna short L_ebcf
L_ebcc: jmp near L_ea50
L_ebcf: shl ax,1
L_ebd1: xchg ax,bx
L_ebd2: jmp word near [cs:bx+csi_command_table]
L_ebd7: nop
csi_command_table:
 dw L_ea46
 dw L_ea50
 dw L_ea46
 dw L_eba2
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_eaae
 dw L_ea50
 dw L_eafa
 dw L_ea50
 dw L_ea50
 dw L_eba8
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_e894
 dw L_e538
 dw L_e554
 dw L_e570
 dw L_e58c
 dw L_e8ea
 dw L_e900
 dw L_e91c
 dw L_e4c4
 dw L_ea50
 dw L_e7ac
 dw L_e802
 dw L_e8b0
 dw L_e8c6
 dw L_ea50
 dw L_ea50
 dw L_e878
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_e850
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_ea50
 dw L_e9de
 dw L_ea50
 dw L_ea50
 dw L_e4c4
 dw L_ea5a
 dw L_e944
 dw L_e9d8
 dw L_ea50
 dw L_ea50
 dw L_e94c
 dw L_e5a2
 dw L_ea2c
 dw L_ea50
 dw L_ea50
 dw L_ea8e
 dw L_e952
 dw L_ea32
 dw L_ea50
 dw L_ea3c
