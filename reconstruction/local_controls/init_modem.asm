; Original Alt-J Init Modem entry CS:3A25..3A54,48 bytes.
; REA ev_63c75f97423f6a94b44eaf6a4e4d6239482b070fc467c03a0d5d971cd24db928.
; Cdecl DS=SS. Sends configured initialization only; restores duplex/pacing.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef INIT_MODEM_OMF
SEGMENT MODEM_INIT_NATIVE_CODE public align=16 class=FARCODE use16
extern modem_send_local_echo,modem_send_pacing_units,modem_init_string,modem_send_original
global local_init_modem_3a25
%else
ORG 0x3a25
%define modem_send_local_echo 0x1d1a
%define modem_send_pacing_units 0x1d68
%define modem_init_string 0x1b9c
%define modem_send_original 0x48cc
%endif
local_init_modem_3a25:
 push di
 push si
 mov di,[modem_send_local_echo]
 mov word [modem_send_local_echo],0
 mov si,[modem_send_pacing_units]
 mov_load ax,si
 cmp ax,strict word 30
 jge short .ready
 mov ax,30
.ready:
 mov [modem_send_pacing_units],ax
 mov ax,modem_init_string
 push ax
 call modem_send_original
 pop bx
 mov [modem_send_local_echo],di
 mov [modem_send_pacing_units],si
 pop si
 pop di
 ret
