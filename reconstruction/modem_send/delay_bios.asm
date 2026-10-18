; Actual PCPlus2.01 resident6b98..6bb6, 30 exact bytes.
; REA assembly Evidence ev_cc5df7fd3b4baa1350abfad9245198f09d55989c263134af069ea519ff7a51f9.
BITS 16
CPU 8086
%ifdef MODEM_SEND_OMF
SEGMENT _TEXT public class=CODE use16
global modem_send_delay_bios
%else
ORG 0x6b98
%endif
%include "encodings.inc"
modem_send_delay_bios:
L_6b98: mov_load bx,sp
L_6b9a: mov dx, word [bx + 0x2]
L_6b9d: inc dx
L_6b9e: sti
L_6b9f: xor_load cx,cx
L_6ba1: mov es, cx
L_6ba3: mov bx, 0x46c
L_6ba6: mov ax, word es:[bx]
L_6ba9: cmp ax, word es:[bx]
L_6bac: jz L_6ba9
L_6bae: inc cx
L_6baf: cmp_load cx,dx
L_6bb1: jc L_6ba6
L_6bb3: ret 0x2
