; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_handshake_enter
global session_at_d754
global session_at_d757
global session_at_d75a
global session_at_d75c
global session_at_d75f
global session_at_d762
global session_at_d765
global session_at_d768
global session_at_d76b
global session_at_d770
global session_at_d775
global session_at_d777
global session_at_d77c
global session_at_d77e
global session_at_d783
global session_at_d785
global session_at_d78a
global session_at_d78c
global session_at_d790
global session_at_d792
global session_at_d797
global session_at_d79c
global session_at_d79e
global session_at_d7a3
global session_at_d7a5
global session_at_d7a8
global session_at_d7a9
global session_at_d7aa
global session_at_d7ac
global session_at_d7ad
global session_at_d7ae
global session_at_d7b1
global session_at_d7b6
global session_at_d7b8
global session_at_d7bb
global session_at_d7bc
global session_at_d7c0
global session_at_d7c2
global session_at_d7c4
global session_at_d7c8
global session_at_d7cb
global session_at_d7cd
global session_at_d7cf
global session_at_d7d2
global session_at_d7d7
global session_at_d7da
global session_at_d7df
global session_at_d7e4
global session_at_d7e6
global session_at_d7e9
global session_at_d7ec
global session_at_d7ee
global session_at_d7f0
global session_at_d7f3
global session_at_d7f5
global session_at_d7f7
global session_at_d7fa
global session_at_d7fb
global session_at_d7fe
global session_at_d801
global session_at_d805
global session_at_d808
global session_at_d80b
global session_at_d80c
global session_at_d80f
global session_at_d813
global session_at_d815
global session_at_d818
global session_at_d81b
global session_at_d81e
global session_at_d81f
global session_at_d821
global session_at_d824
global session_at_d829
global session_at_d82b
global session_at_d830
global session_at_d832
global session_at_d835
global session_at_d838
global session_at_d839
global session_at_d83c
global session_at_d83f
global session_at_d840
global session_at_d841
global session_at_d843
global session_at_d844
global session_at_d845
global session_at_d846
global session_at_d849
global session_at_d84b
global session_at_d84d
global session_at_d850
global session_at_d852
global session_at_d855
global session_at_d856
global session_at_d859
global session_at_d85b
global session_at_d85c
global session_at_d861
global session_at_d863
global session_at_d866
global session_at_d869
global session_at_d86b
global session_at_d86d
global session_at_d870
global session_at_d874
global session_at_d876
global session_at_d878
global session_at_d87b
extern session_buffer_used
extern session_carrier_present
extern session_context_enter
extern session_delay_ticks
extern session_failure_cleanup_argument
extern session_failure_return
extern session_file_close_boundary
extern session_file_handle
extern session_integrity_labels
extern session_last_block
extern session_local_cancel
extern session_protocol
extern session_protocol12_boundary
extern session_protocol9_boundary
extern session_queued_count
extern session_send_nak
extern session_status
extern session_streaming_mode
extern session_transmit_byte
extern session_ui_attribute
extern session_ui_print
extern session_wait
%else
ORG 0xd752
%define session_buffer_used 0xcd34
%define session_carrier_present 0x4861
%define session_context_enter 0xd87c
%define session_delay_ticks 0x6b98
%define session_failure_cleanup_argument 0xd731
%define session_failure_return 0xd734
%define session_file_close_boundary 0x8318
%define session_file_handle 0xcbaa
%define session_integrity_labels 0x2e44
%define session_last_block 0xcc9a
%define session_local_cancel 0x3f4b
%define session_protocol 0x3996
%define session_protocol12_boundary 0xd077
%define session_protocol9_boundary 0xd06b
%define session_queued_count 0x8e20
%define session_send_nak 0x40b9
%define session_status 0xe498
%define session_streaming_mode 0xcdcc
%define session_transmit_byte 0xab0b
%define session_ui_attribute 0x1f76
%define session_ui_print 0x6bf0
%define session_wait 0xf070
%endif
%include "encodings.inc"
session_handshake_enter: sub_load ax,ax
session_at_d754: mov [session_buffer_used],ax
session_at_d757: mov [session_last_block],ax
session_at_d75a: sub_load di,di
session_at_d75c: mov [bp-0x14],di
session_at_d75f: mov [bp-0x4],di
session_at_d762: mov ax,0xffff
session_at_d765: mov [bp-0x2],ax
session_at_d768: mov [bp-0x10],ax
session_at_d76b: mov word [bp-0x8],0x43
session_at_d770: cmp word [session_protocol],0x9
session_at_d775: jnz short session_at_d77e
session_at_d777: mov word [bp-0x8],0x57
session_at_d77c: jmp short session_at_d797
session_at_d77e: cmp word [session_protocol],0xc
session_at_d783: jnz short session_at_d78c
session_at_d785: mov word [bp-0x8],0x55
session_at_d78a: jmp short session_at_d797
session_at_d78c: cmp [session_streaming_mode],di
session_at_d790: jz short session_at_d797
session_at_d792: mov word [bp-0x8],0x47
session_at_d797: mov word [bp-0xa],0x0
session_at_d79c: jmp short session_at_d80f
session_at_d79e: cmp word [session_protocol],0xc
session_at_d7a3: jnz short session_at_d7ae
session_at_d7a5: call session_protocol12_boundary
session_at_d7a8: pop si
session_at_d7a9: pop di
session_at_d7aa: mov_load sp,bp
session_at_d7ac: pop bp
session_at_d7ad: ret
session_at_d7ae: mov di,0x1
session_at_d7b1: cmp word [session_streaming_mode],0x0
session_at_d7b6: jnz short session_at_d7cb
session_at_d7b8: mov ax,0x93e
session_at_d7bb: push ax
session_at_d7bc: push word [session_ui_attribute]
session_at_d7c0: mov_load bx,di
session_at_d7c2: shl bx,1
session_at_d7c4: push word [bx+session_integrity_labels]
session_at_d7c8: call session_ui_print
session_at_d7cb: or_load di,di
session_at_d7cd: jz short session_at_d7d2
session_at_d7cf: jmp near session_context_enter
session_at_d7d2: mov word [bp-0x6],0xa
session_at_d7d7: call session_send_nak
session_at_d7da: mov word [bp-0xa],0x9
session_at_d7df: cmp word [session_queued_count],0x0
session_at_d7e4: jnz short session_at_d85c
session_at_d7e6: mov ax,[bp-0xa]
session_at_d7e9: dec word [bp-0xa]
session_at_d7ec: or_load ax,ax
session_at_d7ee: jz short session_at_d85c
session_at_d7f0: call session_local_cancel
session_at_d7f3: or_load ax,ax
session_at_d7f5: jz short session_at_d846
session_at_d7f7: mov ax,0xb
session_at_d7fa: push ax
session_at_d7fb: call session_status
session_at_d7fe: add sp,0x2
session_at_d801: push word [session_file_handle]
session_at_d805: call session_file_close_boundary
session_at_d808: jmp near session_failure_cleanup_argument
session_at_d80b: nop
session_at_d80c: inc word [bp-0xa]
session_at_d80f: cmp word [bp-0xa],0x3
session_at_d813: jnl short session_at_d7b1
session_at_d815: push word [bp-0x8]
session_at_d818: call session_transmit_byte
session_at_d81b: call session_wait
session_at_d81e: inc ax
session_at_d81f: jnz short session_at_d824
session_at_d821: jmp near session_failure_return
session_at_d824: cmp word [session_queued_count],0x0
session_at_d829: jz short session_at_d80c
session_at_d82b: cmp word [session_protocol],0x9
session_at_d830: jz short session_at_d835
session_at_d832: jmp near session_at_d79e
session_at_d835: lea ax,[bp-0x56]
session_at_d838: push ax
session_at_d839: call session_protocol9_boundary
session_at_d83c: add sp,0x2
session_at_d83f: pop si
session_at_d840: pop di
session_at_d841: mov_load sp,bp
session_at_d843: pop bp
session_at_d844: ret
session_at_d845: nop
session_at_d846: call session_carrier_present
session_at_d849: or_load ax,ax
session_at_d84b: jnz short session_at_d852
session_at_d84d: mov ax,0xf
session_at_d850: jmp short session_at_d7fa
session_at_d852: mov ax,0xa
session_at_d855: push ax
session_at_d856: call session_delay_ticks
session_at_d859: jmp short session_at_d7df
session_at_d85b: nop
session_at_d85c: cmp word [session_queued_count],0x0
session_at_d861: jnz short session_at_d870
session_at_d863: mov ax,[bp-0x6]
session_at_d866: dec word [bp-0x6]
session_at_d869: or_load ax,ax
session_at_d86b: jz short session_at_d870
session_at_d86d: jmp near session_at_d7d7
session_at_d870: cmp word [bp-0x6],0x0
session_at_d874: jnz short session_context_enter
session_at_d876: sub_load ax,ax
session_at_d878: jmp near session_at_d7fa
session_at_d87b: nop
%ifdef TRANSFER_SESSION_OMF
jmp session_context_enter
%endif
