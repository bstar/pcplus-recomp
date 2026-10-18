; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_send_zero
global metadata_at_40ac
global metadata_at_40ad
global metadata_at_40b0
extern metadata_transmit_byte
%else
ORG 0x40aa
%define metadata_transmit_byte 0xab0b
%endif
%include "encodings.inc"
metadata_send_zero: sub_load ax,ax
metadata_at_40ac: push ax
metadata_at_40ad: call metadata_transmit_byte
metadata_at_40b0: ret
