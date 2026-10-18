; Recovered PCPlus2.01 overlay5:e8ad..eaed dial attempt,576 baseline bytes.
; OMF object has explicit unresolved real UI/command/UART/clock services.
; It is not linked into the standalone pure matcher diagnostic.
; REA assembly Evidence ev_5023f79a668e8360dce2412988c12d76db925a146c121f7b7531c9555fabec38.
BITS 16
CPU 8086
%ifdef MODEM_RESPONSES_OMF
SEGMENT _TEXT public class=CODE use16
global modem_dial_attempt_original
extern dial_abort_original
extern dial_autobaud
extern dial_baud_index
extern dial_baud_table
extern dial_carrier_present
extern dial_character_delay
extern dial_connected_ui
extern dial_cursor_position
extern dial_cursor_refresh
extern dial_edit_number
extern dial_format_integer
extern dial_key_pending
extern dial_local_echo
extern dial_parse_integer
extern dial_prefix
extern dial_read_key
extern dial_resource_3f9c
extern dial_resource_6626
extern dial_resource_6686
extern dial_resource_6a00
extern dial_resource_6a08
extern dial_resource_6a10
extern dial_resource_6a18
extern dial_resource_7127
extern dial_seconds
extern dial_send_command
extern dial_set_baud
extern dial_state_e464
extern dial_state_e46a
extern dial_state_e46c
extern dial_state_e46e
extern dial_state_e480
extern dial_suffix
extern dial_timeout_seconds
extern dial_uart_flush
extern dial_ui_attribute
extern dial_ui_choices
extern dial_ui_draw_text
extern dial_ui_printf
extern modem_response_available
extern modem_response_match_original
extern modem_response_slots
%else
ORG 0xe8ad
%define dial_ui_attribute 0x1f7a
%define dial_local_echo 0x1d1a
%define dial_character_delay 0x1d68
%define dial_prefix 0x1bcb
%define dial_suffix 0x1be4
%define modem_response_available 0x8e20
%define dial_timeout_seconds 0x1b8e
%define modem_response_slots 0x1c48
%define dial_autobaud 0x1b92
%define dial_baud_index 0x1b86
%define dial_baud_table 0x3270
%define dial_state_e46c 0xe46c
%define dial_state_e46e 0xe46e
%define dial_state_e464 0xe464
%define dial_state_e480 0xe480
%define dial_state_e46a 0xe46a
%define dial_resource_7127 0x7127
%define dial_resource_6626 0x6626
%define dial_resource_3f9c 0x3f9c
%define dial_resource_6686 0x6686
%define dial_resource_6a10 0x6a10
%define dial_resource_6a18 0x6a18
%define dial_resource_6a08 0x6a08
%define dial_resource_6a00 0x6a00
%define dial_baud_table 0x3270
%define dial_carrier_present 0xaa5c
%define dial_abort_original 0xec0e
%define dial_ui_choices 0x498b
%define dial_ui_draw_text 0x6bf0
%define dial_seconds 0x3323
%define modem_response_match_original 0x4a1d
%define dial_uart_flush 0xabca
%define dial_send_command 0x48cc
%define dial_key_pending 0x6530
%define dial_read_key 0x7878
%define dial_format_integer 0x8e6c
%define dial_edit_number 0x7880
%define dial_parse_integer 0x984e
%define dial_ui_printf 0x75e8
%define dial_cursor_position 0x6e66
%define dial_cursor_refresh 0x6dca
%define dial_set_baud 0xac27
%define dial_connected_ui 0x3616
%endif
%include "encodings.inc"
modem_dial_attempt_original:
L_e8ad: push bp
L_e8ae: mov_load bp,sp
L_e8b0: sub sp, 0x8
L_e8b3: push di
L_e8b4: push si
L_e8b5: call dial_carrier_present
L_e8b8: or_load ax,ax
L_e8ba: jz L_e8bf
L_e8bc: call dial_abort_original
L_e8bf: push word [dial_state_e46c]
L_e8c3: push word [dial_ui_attribute]
L_e8c7: sub_load ax,ax
L_e8c9: push ax
L_e8ca: call dial_ui_choices
L_e8cd: pop bx
L_e8ce: push ax
L_e8cf: call dial_ui_draw_text
L_e8d2: push word [dial_state_e46e]
L_e8d6: push word [dial_ui_attribute]
L_e8da: mov ax, dial_resource_7127
L_e8dd: push ax
L_e8de: call dial_ui_draw_text
L_e8e1: call dial_seconds
L_e8e4: mov word [bp + -0x4], ax
L_e8e7: mov di, word [dial_local_echo]
L_e8eb: sub_load ax,ax
L_e8ed: mov word [bp + -0x2], ax
L_e8f0: mov [dial_local_echo], ax
L_e8f3: mov si, word [dial_character_delay]
L_e8f7: mov_load ax,si
L_e8f9: cmp ax,strict word 0x1e
L_e8fc: jge L_e901
L_e8fe: mov ax, 0x1e
L_e901: mov [dial_character_delay], ax
L_e904: mov ax, 0x1
L_e907: push ax
L_e908: call modem_response_match_original
L_e90b: pop bx
L_e90c: call dial_uart_flush
L_e90f: mov ax, dial_prefix
L_e912: push ax
L_e913: call dial_send_command
L_e916: pop bx
L_e917: push word [bp + 0x4]
L_e91a: call dial_send_command
L_e91d: pop bx
L_e91e: mov ax, dial_suffix
L_e921: push ax
L_e922: call dial_send_command
L_e925: pop bx
L_e926: mov word [dial_character_delay], si
L_e92a: mov word [dial_local_echo], di
L_e92e: call dial_seconds
L_e931: cmp ax, word [bp + -0x4]
L_e934: jz L_e95f
L_e936: call dial_seconds
L_e939: mov word [bp + -0x4], ax
L_e93c: mov ax, [dial_timeout_seconds]
L_e93f: inc word [bp + -0x2]
L_e942: cmp word [bp + -0x2], ax
L_e945: jle L_e94a
L_e947: jmp near L_eaa5
L_e94a: push word [bp + -0x2]
L_e94d: mov ax, dial_resource_6626
L_e950: push ax
L_e951: push word [dial_ui_attribute]
L_e955: push word [dial_state_e46e]
L_e959: call dial_ui_printf
L_e95c: add sp, 0x8
L_e95f: call dial_key_pending
L_e962: or_load ax,ax
L_e964: jz L_e9e5
L_e966: call dial_read_key
L_e969: sub ax,strict word 0x1b
L_e96c: jnz L_e971
L_e96e: jmp near L_ea6c
L_e971: sub ax,strict word 0x5
L_e974: jnz L_e979
L_e976: jmp near L_ea8a
L_e979: sub ax,strict word 0x4ee0
L_e97c: jz L_e988
L_e97e: sub ax,strict word 0x400
L_e981: jnz L_e986
L_e983: jmp near L_ea51
L_e986: jmp short L_e9e5
L_e988: mov ax, 0xa
L_e98b: push ax
L_e98c: lea ax, [bp + -0x8]
L_e98f: push ax
L_e990: push word [dial_timeout_seconds]
L_e994: call dial_format_integer
L_e997: add sp, 0x6
L_e99a: push word [dial_state_e464]
L_e99e: push word [dial_ui_attribute]
L_e9a2: lea ax, [bp + -0x8]
L_e9a5: push ax
L_e9a6: push ax
L_e9a7: mov ax, 0x3
L_e9aa: push ax
L_e9ab: mov ax, dial_resource_3f9c
L_e9ae: push ax
L_e9af: call dial_edit_number
L_e9b2: or_load ax,ax
L_e9b4: jle L_e9c1
L_e9b6: lea ax, [bp + -0x8]
L_e9b9: push ax
L_e9ba: call dial_parse_integer
L_e9bd: pop bx
L_e9be: mov [dial_timeout_seconds], ax
L_e9c1: push word [dial_timeout_seconds]
L_e9c5: mov ax, dial_resource_6626
L_e9c8: push ax
L_e9c9: push word [dial_ui_attribute]
L_e9cd: push word [dial_state_e464]
L_e9d1: call dial_ui_printf
L_e9d4: add sp, 0x8
L_e9d7: push word [dial_state_e480]
L_e9db: mov ax, 0xb
L_e9de: push ax
L_e9df: call dial_cursor_position
L_e9e2: call dial_cursor_refresh
L_e9e5: cmp word [modem_response_available], 0x0
L_e9ea: jnz L_e9ef
L_e9ec: jmp near L_e92e
L_e9ef: sub_load ax,ax
L_e9f1: push ax
L_e9f2: call modem_response_match_original
L_e9f5: pop bx
L_e9f6: mov_load si,ax
L_e9f8: cmp si, -0x1
L_e9fb: jz L_ea1a
L_e9fd: or_load si,si
L_e9ff: jl L_ea1a
L_ea01: cmp si, 0x7
L_ea04: jge L_ea1a
L_ea06: mov cl, 0x4
L_ea08: shl ax, cl
L_ea0a: add ax, modem_response_slots
L_ea0d: push ax
L_ea0e: mov ax, dial_resource_6686
L_ea11: push ax
L_ea12: mov ax, [dial_ui_attribute]
L_ea15: or al, 0x80
L_ea17: push ax
L_ea18: jmp short L_ea2f
L_ea1a: cmp si, -0x1
L_ea1d: jz L_ea39
L_ea1f: mov cl, 0x4
L_ea21: shl ax, cl
L_ea23: add ax, modem_response_slots
L_ea26: push ax
L_ea27: mov ax, dial_resource_6686
L_ea2a: push ax
L_ea2b: push word [dial_ui_attribute]
L_ea2f: push word [dial_state_e46a]
L_ea33: call dial_ui_printf
L_ea36: add sp, 0x8
L_ea39: cmp si, 0x6
L_ea3c: jle L_ea43
L_ea3e: cmp si, 0xb
L_ea41: jl L_eabb
L_ea43: or_load si,si
L_ea45: jl L_ea4c
L_ea47: cmp si, 0x7
L_ea4a: jl L_ea4f
L_ea4c: jmp near L_e92e
L_ea4f: jmp short L_eabf
L_ea51: mov ax, dial_resource_6a10
L_ea54: push ax
L_ea55: mov ax, dial_resource_6686
L_ea58: push ax
L_ea59: push word [dial_ui_attribute]
L_ea5d: push word [dial_state_e46a]
L_ea61: call dial_ui_printf
L_ea64: add sp, 0x8
L_ea67: mov ax, 0x3
L_ea6a: jmp short L_eae7
L_ea6c: mov ax, dial_resource_6a18
L_ea6f: push ax
L_ea70: mov ax, dial_resource_6686
L_ea73: push ax
L_ea74: push word [dial_ui_attribute]
L_ea78: push word [dial_state_e46a]
L_ea7c: call dial_ui_printf
L_ea7f: add sp, 0x8
L_ea82: call dial_abort_original
L_ea85: mov ax, 0x1b
L_ea88: jmp short L_eae7
L_ea8a: mov ax, dial_resource_6a08
L_ea8d: push ax
L_ea8e: mov ax, dial_resource_6686
L_ea91: push ax
L_ea92: push word [dial_ui_attribute]
L_ea96: push word [dial_state_e46a]
L_ea9a: call dial_ui_printf
L_ea9d: add sp, 0x8
L_eaa0: mov ax, 0x2
L_eaa3: jmp short L_eae7
L_eaa5: mov ax, dial_resource_6a00
L_eaa8: push ax
L_eaa9: mov ax, dial_resource_6686
L_eaac: push ax
L_eaad: push word [dial_ui_attribute]
L_eab1: push word [dial_state_e46a]
L_eab5: call dial_ui_printf
L_eab8: add sp, 0x8
L_eabb: sub_load ax,ax
L_eabd: jmp short L_eae7
L_eabf: cmp word [dial_autobaud], 0x0
L_eac4: jz L_eae1
L_eac6: cmp word [dial_baud_index], si
L_eaca: jz L_eae1
L_eacc: mov word [dial_baud_index], si
L_ead0: shl si, 0x1
L_ead2: shl si, 0x1
L_ead4: push word [si + dial_baud_table+2]
L_ead8: push word [si + dial_baud_table]
L_eadc: call dial_set_baud
L_eadf: pop bx
L_eae0: pop bx
L_eae1: call dial_connected_ui
L_eae4: mov ax, 0x1
L_eae7: pop si
L_eae8: pop di
L_eae9: mov_load sp,bp
L_eaeb: pop bp
L_eaec: ret
