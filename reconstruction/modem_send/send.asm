; Actual PCPlus2.01 resident48cc..4934, 104 exact bytes.
; REA assembly Evidence ev_3a29c9753cf6188658686eb46944e813fddeb172758c9bded7dc265f9aeac907.
BITS 16
CPU 8086
%ifdef MODEM_SEND_OMF
SEGMENT _TEXT public class=CODE use16
global modem_send_original
extern modem_send_pause_marker
extern modem_send_local_echo
extern modem_send_pacing_units
extern modem_expand_original
extern modem_send_delay_bios
extern modem_send_delay_calibrated
extern uart_transmit_byte
extern modem_send_echo_character
%else
ORG 0x48cc
%define modem_send_pause_marker 0x1d66
%define modem_send_local_echo 0x1d1a
%define modem_send_pacing_units 0x1d68
%define modem_expand_original 0x4934
%define modem_send_delay_bios 0x6b98
%define modem_send_delay_calibrated 0x6b72
%define uart_transmit_byte 0xab0b
%define modem_send_echo_character 0x0610
%endif
%include "encodings.inc"
modem_send_original:
L_48cc: push bp
L_48cd: mov_load bp,sp
L_48cf: sub sp, 0x82
L_48d3: push si
L_48d4: lea ax, [bp + 0xff7e]
L_48d8: push ax
L_48d9: push word [bp + 0x4]
L_48dc: call modem_expand_original
L_48df: pop bx
L_48e0: pop bx
L_48e1: lea si, [bp + 0xff7e]
L_48e5: jmp short L_4927
L_48e7: mov al, [modem_send_pause_marker]
L_48ea: cmp byte [bp + -0x1], al
L_48ed: jnz L_48f8
L_48ef: mov ax, 0x9
L_48f2: push ax
L_48f3: call modem_send_delay_bios
L_48f6: jmp short L_4927
L_48f8: cmp byte [bp + -0x1], 0xff
L_48fc: jnz L_4906
L_48fe: sub_load ax,ax
L_4900: push ax
L_4901: call uart_transmit_byte
L_4904: jmp short L_4927
L_4906: cmp word [modem_send_local_echo], 0x0
L_490b: jz L_4917
L_490d: mov al, byte [bp + -0x1]
L_4910: sub_load ah,ah
L_4912: push ax
L_4913: call modem_send_echo_character
L_4916: pop bx
L_4917: mov al, byte [bp + -0x1]
L_491a: sub_load ah,ah
L_491c: push ax
L_491d: call uart_transmit_byte
L_4920: push word [modem_send_pacing_units]
L_4924: call modem_send_delay_calibrated
L_4927: lodsb
L_4928: mov byte [bp + -0x1], al
L_492b: or_load al,al
L_492d: jnz L_48e7
L_492f: pop si
L_4930: mov_load sp,bp
L_4932: pop bp
L_4933: ret
