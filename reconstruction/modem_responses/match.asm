; Recovered original PCPlus2.01 resident4a1d..4aa7. No original data copied.
; REA assembly Evidence ev_eaf6bfcee78dea8d82da1fec58a76a1138dcf75801e5e52cc3063094472bfc9e.
BITS 16
CPU 8086
%ifdef MODEM_RESPONSES_OMF
SEGMENT _TEXT public class=CODE use16
global modem_response_match_original
extern modem_response_slots,modem_response_cursors,modem_response_available,modem_response_read_byte
%else
ORG 0x4a1d
%define modem_response_slots 0x1c48
%define modem_response_cursors 0x8f58
%define modem_response_available 0x8e20
%define modem_response_read_byte 0xaad9
%endif
%include "encodings.inc"
modem_response_match_original:
L_4a1d: push bp
L_4a1e: mov_load bp,sp
L_4a20: sub sp, 0x6
L_4a23: push di
L_4a24: push si
L_4a25: cmp word [bp + 0x4], 0x0
L_4a29: jz L_4a41
L_4a2b: mov dx, modem_response_slots
L_4a2e: mov bx, modem_response_cursors
L_4a31: cmp bx, modem_response_cursors+22
L_4a35: jnc L_4a9e
L_4a37: inc bx
L_4a38: inc bx
L_4a39: mov word [bx + -0x2], dx
L_4a3c: add dx, 0x10
L_4a3f: jmp L_4a31
L_4a41: cmp word [modem_response_available], 0x0
L_4a46: jz L_4a9e
L_4a48: mov ax, 0x1
L_4a4b: push ax
L_4a4c: call modem_response_read_byte
L_4a4f: mov byte [bp + -0x3], al
L_4a52: mov word [bp + -0x6], 0x0
L_4a57: mov di, modem_response_slots
L_4a5a: mov word [bp + -0x2], modem_response_cursors
L_4a5f: mov si, word [bp + -0x2]
L_4a62: mov dx, word [bp + -0x6]
L_4a65: cmp si, modem_response_cursors+22
L_4a69: jnc L_4a41
L_4a6b: mov bx, word [si]
L_4a6d: cmp byte [bx], 0x0
L_4a70: jz L_4a96
L_4a72: mov al, byte [bp + -0x3]
L_4a75: cmp byte [bx], al
L_4a77: jnz L_4a86
L_4a79: inc word [si]
L_4a7b: mov bx, word [si]
L_4a7d: cmp byte [bx], 0x0
L_4a80: jnz L_4a96
L_4a82: mov_load ax,dx
L_4a84: jmp L_4aa1
L_4a86: mov al, byte [di]
L_4a88: cmp byte [bp + -0x3], al
L_4a8b: jnz L_4a92
L_4a8d: lea ax, [di + 0x1]
L_4a90: jmp L_4a94
L_4a92: mov_load ax,di
L_4a94: mov word [si], ax
L_4a96: add di, 0x10
L_4a99: inc si
L_4a9a: inc si
L_4a9b: inc dx
L_4a9c: jmp L_4a65
L_4a9e: mov ax, 0xffff
L_4aa1: pop si
L_4aa2: pop di
L_4aa3: mov_load sp,bp
L_4aa5: pop bp
L_4aa6: ret
