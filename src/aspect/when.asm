; Recovered PCPlus2.01 WHEN/CWHEN and receive monitor. Original SHA256
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; REA E8FC ev_2655c976f9495aeb77f30f95468db58ba4e652743a7959afa9d3f6e924f9d059
; 534E ev_ecf427221dda369399a0b942379ff7decf9928213296f2c904836bee01c029e9
; 53C2 ev_5b047fe51704da0fc1e29d7595425c9cb5d81b0816ac153008bbedb5eb738035
; DS=SS; 8086. monitor/trigger RET2, other exports near RET.
; Four86-byte records: three ordinary slots and one disconnect action.
; C7/C8 call actual flow/frame owners; handler execution is deferred until
; current receive service returns. Shared flow_wait_gate is native E382.
; String reader is caller-clean; the pushed40 is consumed by later memcpy.
; Registration truncates40, NUL-terminates, and caret-decodes pattern in place.
; Monitor receives already translated leads only; parser continuations bypass it.
; Carrier, keyboard/UI and host-poll remain explicit external device services.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_WHEN_FLAT
%if ASPECT_WHEN_UNIT=1
ORG 0xe8c9
%endif
%if ASPECT_WHEN_UNIT=2
ORG 0x534e
%endif
%if ASPECT_WHEN_UNIT=3
ORG 0x53c2
%endif
%if ASPECT_WHEN_UNIT=4
ORG 0x4de9
%endif
%define aspect_string_read 0xdf04
%define aspect_string_upper 0x9128
%define erase_move_bytes 0x85b4
%define aspect_dispatch_read 0x4cb4
%define aspect_flow_read_dword 0xe176
%define aspect_console_decode 0x4934
%define aspect_string_option_flag 0xe0e4
%define aspect_string_bounded_integer 0xdd68
%define aspect_serial_upper_byte 0x8252
%define aspect_serial_send_formatted 0x48cc
%define aspect_flow_call 0xcd8f
%define aspect_flow_push_frame 0xcd9b
%define aspect_when_host_poll 0xdde
%define aspect_when_carrier 0xaa5c
%define aspect_when_key_ready 0x651a
%define aspect_when_read_key 0x64fe
%define aspect_when_confirm_abort 0x4e6b
%define aspect_when_abort 0x4ebc
%define aspect_when_dispatch_key 0x1604
%define aspect_when_records 0xe1a0
%define aspect_when_case_sensitive 0xe398
%define aspect_when_active_count 0xe2f8
%define aspect_when_disconnect_armed 0xe2fa
%define aspect_flow_wait_gate 0xe382
%define aspect_when_pending_key 0x397a
%define aspect_when_keyboard_disabled 0xe380
%define aspect_when_last_key 0xcffa
%if ASPECT_WHEN_UNIT!=1
%define aspect_when_cancel 0xe8c9
%endif
%if ASPECT_WHEN_UNIT!=1
%define aspect_when_register 0xe8fc
%endif
%if ASPECT_WHEN_UNIT!=1
%define aspect_when_slot 0xe9df
%endif
%if ASPECT_WHEN_UNIT!=2
%define aspect_when_monitor 0x534e
%endif
%if ASPECT_WHEN_UNIT!=3
%define aspect_when_trigger 0x53c2
%endif
%if ASPECT_WHEN_UNIT!=4
%define aspect_when_service 0x4de9
%endif
%else
%define ASPECT_WHEN_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_when_cancel
global aspect_when_register
global aspect_when_slot
global aspect_when_monitor
global aspect_when_trigger
global aspect_when_service
extern aspect_string_read
extern aspect_string_upper
extern erase_move_bytes
extern aspect_dispatch_read
extern aspect_flow_read_dword
extern aspect_console_decode
extern aspect_string_option_flag
extern aspect_string_bounded_integer
extern aspect_serial_upper_byte
extern aspect_serial_send_formatted
extern aspect_flow_call
extern aspect_flow_push_frame
extern aspect_when_host_poll
extern aspect_when_carrier
extern aspect_when_key_ready
extern aspect_when_read_key
extern aspect_when_confirm_abort
extern aspect_when_abort
extern aspect_when_dispatch_key
extern aspect_when_records
extern aspect_when_case_sensitive
extern aspect_when_active_count
extern aspect_when_disconnect_armed
extern aspect_flow_wait_gate
extern aspect_when_pending_key
extern aspect_when_keyboard_disabled
extern aspect_when_last_key
%endif
%if ASPECT_WHEN_UNIT=0 || ASPECT_WHEN_UNIT=1
aspect_when_cancel:
when_loc_e8c9:
 push si
when_loc_e8ca:
 call aspect_when_slot
when_loc_e8cd:
 mov_load si, ax
when_loc_e8cf:
 cmp si, 0x2
when_loc_e8d2:
 jle when_loc_e8dc
when_loc_e8d4:
 mov word [aspect_when_disconnect_armed], 0x0
when_loc_e8da:
 pop si
when_loc_e8db:
 ret
when_loc_e8dc:
 mov cx, 0x56
when_loc_e8df:
 imul cx
when_loc_e8e1:
 mov_load bx, ax
when_loc_e8e3:
 cmp word [bx + aspect_when_records+84], 0x0
when_loc_e8e8:
 jz when_loc_e8fa
when_loc_e8ea:
 mov_load ax, si
when_loc_e8ec:
 imul cx
when_loc_e8ee:
 mov_load bx, ax
when_loc_e8f0:
 mov word [bx + aspect_when_records+84], 0x0
when_loc_e8f6:
 dec word [aspect_when_active_count]
when_loc_e8fa:
 pop si
when_loc_e8fb:
 ret
aspect_when_register:
when_loc_e8fc:
 push bp
when_loc_e8fd:
 mov_load bp, sp
when_loc_e8ff:
 sub sp, 0x4
when_loc_e902:
 push di
when_loc_e903:
 push si
when_loc_e904:
 call aspect_when_slot
when_loc_e907:
 mov_load si, ax
when_loc_e909:
 cmp si, 0x2
when_loc_e90c:
 jg when_loc_e938
when_loc_e90e:
 mov ax, 0x28
when_loc_e911:
 push ax
when_loc_e912:
 cmp word [aspect_when_case_sensitive], 0x0
when_loc_e917:
 jnz when_loc_e923
when_loc_e919:
 call aspect_string_read
when_loc_e91c:
 push ax
when_loc_e91d:
 call aspect_string_upper
when_loc_e920:
 pop bx
when_loc_e921:
 jmp short when_loc_e926
when_loc_e923:
 call aspect_string_read
when_loc_e926:
 push ax
when_loc_e927:
 mov_load ax, si
when_loc_e929:
 mov cx, 0x56
when_loc_e92c:
 imul cx
when_loc_e92e:
 add ax, aspect_when_records+1
when_loc_e931:
 push ax
when_loc_e932:
 call erase_move_bytes
when_loc_e935:
 add sp, 0x6
when_loc_e938:
 call aspect_dispatch_read
when_loc_e93b:
 mov_load di, ax
when_loc_e93d:
 cmp di, 0x32
when_loc_e940:
 jnz when_loc_e95d
when_loc_e942:
 mov ax, 0x28
when_loc_e945:
 push ax
when_loc_e946:
 call aspect_string_read
when_loc_e949:
 push ax
when_loc_e94a:
 mov_load ax, si
when_loc_e94c:
 mov cx, 0x56
when_loc_e94f:
 imul cx
when_loc_e951:
 add ax, aspect_when_records+42
when_loc_e954:
 push ax
when_loc_e955:
 call erase_move_bytes
when_loc_e958:
 add sp, 0x6
when_loc_e95b:
 jmp short when_loc_e983
when_loc_e95d:
 call aspect_dispatch_read
when_loc_e960:
 mov_load di, ax
when_loc_e962:
 call aspect_flow_read_dword
when_loc_e965:
 mov_load cx, ax
when_loc_e967:
 mov_load ax, si
when_loc_e969:
 mov bx, 0x56
when_loc_e96c:
 mov word [bp + -0x4], cx
when_loc_e96f:
 mov word [bp + -0x2], dx
when_loc_e972:
 imul bx
when_loc_e974:
 mov_load bx, ax
when_loc_e976:
 mov_load ax, cx
when_loc_e978:
 mov dx, word [bp + -0x2]
when_loc_e97b:
 mov word [bx + aspect_when_records+42], ax
when_loc_e97f:
 mov word [bx + aspect_when_records+44], dx
when_loc_e983:
 mov_load ax, si
when_loc_e985:
 mov cx, 0x56
when_loc_e988:
 imul cx
when_loc_e98a:
 mov_load bx, ax
when_loc_e98c:
 mov_load ax, di
when_loc_e98e:
 mov byte [bx + aspect_when_records], al
when_loc_e992:
 sub_load al, al
when_loc_e994:
 mov byte [bx + aspect_when_records+82], al
when_loc_e998:
 mov byte [bx + aspect_when_records+41], al
when_loc_e99c:
 cmp si, 0x2
when_loc_e99f:
 jg when_loc_e9d3
when_loc_e9a1:
 mov_load ax, si
when_loc_e9a3:
 imul cx
when_loc_e9a5:
 mov_load cx, ax
when_loc_e9a7:
 add ax, aspect_when_records+1
when_loc_e9aa:
 push ax
when_loc_e9ab:
 push ax
when_loc_e9ac:
 mov_load di, cx
when_loc_e9ae:
 call aspect_console_decode
when_loc_e9b1:
 pop bx
when_loc_e9b2:
 pop bx
when_loc_e9b3:
 cmp word [di + aspect_when_records+84], 0x0
when_loc_e9b8:
 jnz when_loc_e9be
when_loc_e9ba:
 inc word [aspect_when_active_count]
when_loc_e9be:
 mov_load ax, si
when_loc_e9c0:
 mov cx, 0x56
when_loc_e9c3:
 imul cx
when_loc_e9c5:
 mov_load bx, ax
when_loc_e9c7:
 add bx, aspect_when_records+1
when_loc_e9cb:
 mov_load si, ax
when_loc_e9cd:
 mov word [si + aspect_when_records+84], bx
when_loc_e9d1:
 jmp short when_loc_e9d9
when_loc_e9d3:
 mov word [aspect_when_disconnect_armed], 0x1
when_loc_e9d9:
 pop si
when_loc_e9da:
 pop di
when_loc_e9db:
 mov_load sp, bp
when_loc_e9dd:
 pop bp
when_loc_e9de:
 ret
aspect_when_slot:
when_loc_e9df:
 call aspect_string_option_flag
when_loc_e9e2:
 or_load ax, ax
when_loc_e9e4:
 jz when_loc_e9f1
when_loc_e9e6:
 sub_load ax, ax
when_loc_e9e8:
 push ax
when_loc_e9e9:
 mov ax, 0x2
when_loc_e9ec:
 push ax
when_loc_e9ed:
 call aspect_string_bounded_integer
when_loc_e9f0:
 ret
when_loc_e9f1:
 mov ax, 0x3
when_loc_e9f4:
 ret
%endif
%if ASPECT_WHEN_UNIT=0 || ASPECT_WHEN_UNIT=2
aspect_when_monitor:
when_loc_534e:
 push bp
when_loc_534f:
 mov_load bp, sp
when_loc_5351:
 sub sp, 0x2
when_loc_5354:
 push di
when_loc_5355:
 push si
when_loc_5356:
 cmp word [aspect_when_case_sensitive], 0x0
when_loc_535b:
 jnz when_loc_5367
when_loc_535d:
 push word [bp + 0x4]
when_loc_5360:
 call aspect_serial_upper_byte
when_loc_5363:
 pop bx
when_loc_5364:
 mov word [bp + 0x4], ax
when_loc_5367:
 sub_load di, di
when_loc_5369:
 mov word [bp + -0x2], di
when_loc_536c:
 mov_load si, di
when_loc_536e:
 jmp short when_loc_53b4
when_loc_5370:
 cmp word [si + aspect_when_records+84], 0x0
when_loc_5375:
 jz when_loc_53b0
when_loc_5377:
 mov bx, word [si + aspect_when_records+84]
when_loc_537b:
 mov al, byte [bx]
when_loc_537d:
 sub_load ah, ah
when_loc_537f:
 cmp ax, word [bp + 0x4]
when_loc_5382:
 jz when_loc_539f
when_loc_5384:
 mov al, byte [si + aspect_when_records+1]
when_loc_5388:
 cmp ax, word [bp + 0x4]
when_loc_538b:
 jnz when_loc_5392
when_loc_538d:
 mov ax, 0x1
when_loc_5390:
 jmp short when_loc_5394
when_loc_5392:
 sub_load ax, ax
when_loc_5394:
 add_load ax, si
when_loc_5396:
 add ax, aspect_when_records+1
when_loc_5399:
 mov word [si + aspect_when_records+84], ax
when_loc_539d:
 jmp short when_loc_53b0
when_loc_539f:
 inc word [si + aspect_when_records+84]
when_loc_53a3:
 mov bx, word [si + aspect_when_records+84]
when_loc_53a7:
 cmp byte [bx], 0x0
when_loc_53aa:
 jnz when_loc_53b0
when_loc_53ac:
 push di
when_loc_53ad:
 call aspect_when_trigger
when_loc_53b0:
 add si, 0x56
when_loc_53b3:
 inc di
when_loc_53b4:
 cmp si, 0xac
when_loc_53b8:
 jle when_loc_5370
when_loc_53ba:
 pop si
when_loc_53bb:
 pop di
when_loc_53bc:
 mov_load sp, bp
when_loc_53be:
 pop bp
when_loc_53bf:
 ret 0x2
%endif
%if ASPECT_WHEN_UNIT=0 || ASPECT_WHEN_UNIT=3
aspect_when_trigger:
when_loc_53c2:
 push bp
when_loc_53c3:
 mov_load bp, sp
when_loc_53c5:
 push di
when_loc_53c6:
 push si
when_loc_53c7:
 mov si, word [bp + 0x4]
when_loc_53ca:
 mov_load ax, si
when_loc_53cc:
 mov cx, 0x56
when_loc_53cf:
 imul cx
when_loc_53d1:
 mov_load bx, ax
when_loc_53d3:
 cmp byte [bx + aspect_when_records], 0x32
when_loc_53d8:
 jnz when_loc_53e8
when_loc_53da:
 mov_load ax, si
when_loc_53dc:
 imul cx
when_loc_53de:
 add ax, aspect_when_records+42
when_loc_53e1:
 push ax
when_loc_53e2:
 call aspect_serial_send_formatted
when_loc_53e5:
 pop bx
when_loc_53e6:
 jmp short when_loc_5409
when_loc_53e8:
 inc word [aspect_flow_wait_gate]
when_loc_53ec:
 mov_load ax, si
when_loc_53ee:
 imul cx
when_loc_53f0:
 mov_load bx, ax
when_loc_53f2:
 push word [bx + aspect_when_records+44]
when_loc_53f6:
 push word [bx + aspect_when_records+42]
when_loc_53fa:
 mov_load di, bx
when_loc_53fc:
 call aspect_flow_call
when_loc_53ff:
 cmp byte [di + aspect_when_records], 0xc8
when_loc_5404:
 jnz when_loc_5409
when_loc_5406:
 call aspect_flow_push_frame
when_loc_5409:
 cmp si, 0x2
when_loc_540c:
 jg when_loc_5423
when_loc_540e:
 mov_load ax, si
when_loc_5410:
 mov cx, 0x56
when_loc_5413:
 imul cx
when_loc_5415:
 mov_load bx, ax
when_loc_5417:
 add bx, aspect_when_records+1
when_loc_541b:
 mov_load si, ax
when_loc_541d:
 mov word [si + aspect_when_records+84], bx
when_loc_5421:
 jmp short when_loc_5429
when_loc_5423:
 mov word [aspect_when_disconnect_armed], 0x0
when_loc_5429:
 pop si
when_loc_542a:
 pop di
when_loc_542b:
 mov_load sp, bp
when_loc_542d:
 pop bp
when_loc_542e:
 ret 0x2
%endif
%if ASPECT_WHEN_UNIT=0 || ASPECT_WHEN_UNIT=4
aspect_when_service:
when_loc_4de9:
 call aspect_when_host_poll
when_loc_4dec:
 cmp word [aspect_when_disconnect_armed], 0x0
when_loc_4df1:
 jz when_loc_4e01
when_loc_4df3:
 call aspect_when_carrier
when_loc_4df6:
 or_load ax, ax
when_loc_4df8:
 jnz when_loc_4e01
when_loc_4dfa:
 mov ax, 0x3
when_loc_4dfd:
 push ax
when_loc_4dfe:
 call aspect_when_trigger
when_loc_4e01:
 mov word [aspect_when_pending_key], 0xffff
when_loc_4e07:
 cmp word [aspect_when_keyboard_disabled], 0x0
when_loc_4e0c:
 jnz when_loc_4e31
when_loc_4e0e:
 call aspect_when_key_ready
when_loc_4e11:
 or_load ax, ax
when_loc_4e13:
 jz when_loc_4e31
when_loc_4e15:
 call aspect_when_read_key
when_loc_4e18:
 mov word [aspect_when_last_key], ax
when_loc_4e1b:
 cmp ax, strict word 0x1b
when_loc_4e1e:
 jnz when_loc_4e2e
when_loc_4e20:
 call aspect_when_confirm_abort
when_loc_4e23:
 or_load ax, ax
when_loc_4e25:
 jz when_loc_4e31
when_loc_4e27:
 call aspect_when_abort
when_loc_4e2a:
 mov ax, 0x1
when_loc_4e2d:
 ret
when_loc_4e2e:
 call aspect_when_dispatch_key
when_loc_4e31:
 sub_load ax, ax
when_loc_4e33:
 ret
%endif
