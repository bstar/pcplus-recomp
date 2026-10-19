; Exact PCPlus2.01 native resident4BFF..4C3C end-of-script receive drain.
; REA ev_905383bd77df48ac8e3cb20cc751e7b4261fed54f625a46cd51ddf1eb53f2adf.
; DS=SS; nearRET; BP/SI/DI preserved through declared callees.
; delay andreceive RET2; key_ready RET without consuming a key.
; Native unbounded live drain, not a maintained deadline/ownership policy.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_END_WAIT_FLAT
ORG 0x4bff
%define aspect_end_wait_delay 0x6b72
%define aspect_end_wait_rx_count 0x8e20
%define aspect_end_wait_pattern_count 0xe2f8
%define aspect_end_wait_display 0xe37e
%define aspect_end_wait_receive 0x4c3c
%define aspect_end_wait_key_ready 0x651a
%else
SEGMENT _TEXT public class=CODE use16
global aspect_end_wait
extern aspect_end_wait_delay,aspect_end_wait_rx_count,aspect_end_wait_pattern_count
extern aspect_end_wait_display,aspect_end_wait_receive,aspect_end_wait_key_ready
%endif
aspect_end_wait:
 mov ax,50
 push ax
 call aspect_end_wait_delay
 cmp word [aspect_end_wait_rx_count],0
 jz .done
 mov word [aspect_end_wait_pattern_count],0
 mov word [aspect_end_wait_display],1
.read:
 sub_load ax,ax
 push ax
 call aspect_end_wait_receive
 cmp word [aspect_end_wait_rx_count],0
 jnz .pending
 mov ax,15
 push ax
 call aspect_end_wait_delay
.pending:
 cmp word [aspect_end_wait_rx_count],0
 jz .done
 call aspect_end_wait_key_ready
 or_load ax,ax
 jz .read
.done:
 ret
