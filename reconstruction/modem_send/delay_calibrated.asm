; Actual PCPlus2.01 resident6b72..6b98, 38 exact bytes.
; REA assembly Evidence ev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc.
BITS 16
CPU 8086
%ifdef MODEM_SEND_OMF
SEGMENT _TEXT public class=CODE use16
global modem_send_delay_calibrated
extern modem_send_delay_floor
extern modem_send_delay_count
%else
ORG 0x6b72
%define modem_send_delay_floor 0x7a4e
%define modem_send_delay_count 0x7ac4
%endif
%include "encodings.inc"
modem_send_delay_calibrated:
L_6b72: mov_load bx,sp
L_6b74: mov dx, word [bx + 0x2]
L_6b77: cmp dx, 0x0
L_6b7a: jz L_6b95
L_6b7c: mov ax, ds
L_6b7e: mov es, ax
L_6b80: mov bx, modem_send_delay_floor
L_6b83: mov cx, word [modem_send_delay_count]
L_6b87: sub cx, 0x1
L_6b8a: adc ax, strict word 0x0
L_6b8d: cmp cx, word es:[bx]
L_6b90: jnz L_6b87
L_6b92: dec dx
L_6b93: jnz L_6b83
L_6b95: ret 0x2
