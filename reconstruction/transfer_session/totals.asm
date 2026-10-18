; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_totals_initialize
global session_at_efb2
global session_at_efb5
global session_at_efb8
global session_at_efbb
global session_at_efbe
global session_at_efc1
global session_at_efc4
global session_at_efc7
global session_at_efca
extern session_bytes_high
extern session_bytes_low
extern session_expected_high
extern session_expected_low
extern session_state_cd3a
extern session_state_cd76
extern session_total_high
extern session_total_low
%else
ORG 0xefb0
%define session_bytes_high 0xcb2e
%define session_bytes_low 0xcb2c
%define session_expected_high 0x9008
%define session_expected_low 0x9006
%define session_state_cd3a 0xcd3a
%define session_state_cd76 0xcd76
%define session_total_high 0x8ffc
%define session_total_low 0x8ffa
%endif
%include "encodings.inc"
session_totals_initialize: sub_load ax,ax
session_at_efb2: mov [session_total_high],ax
session_at_efb5: mov [session_total_low],ax
session_at_efb8: mov [session_expected_high],ax
session_at_efbb: mov [session_expected_low],ax
session_at_efbe: mov [session_bytes_high],ax
session_at_efc1: mov [session_bytes_low],ax
session_at_efc4: mov [session_state_cd76],ax
session_at_efc7: mov [session_state_cd3a],ax
session_at_efca: ret
