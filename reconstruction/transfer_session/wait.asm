; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_wait
global session_at_f071
global session_at_f072
global session_at_f074
global session_at_f078
global session_at_f07a
global session_at_f07d
global session_at_f07f
global session_at_f080
global session_at_f085
global session_at_f087
global session_at_f08b
global session_at_f08f
global session_at_f091
global session_at_f093
global session_at_f096
global session_at_f097
global session_at_f09a
global session_at_f09f
global session_at_f0a1
global session_at_f0a2
global session_at_f0a4
global session_at_f0a6
global session_at_f0a9
global session_at_f0ab
global session_at_f0ad
global session_at_f0b0
global session_at_f0b2
global session_at_f0b5
global session_at_f0b8
global session_at_f0b9
global session_at_f0ba
global session_at_f0bb
global session_at_f0bc
global session_at_f0bf
global session_at_f0c1
global session_at_f0c3
global session_at_f0c6
global session_at_f0c7
global session_at_f0ca
global session_at_f0cd
global session_at_f0d0
global session_at_f0d1
global session_at_f0d2
extern session_carrier_present
extern session_delay_ticks
extern session_local_cancel
extern session_queued_count
extern session_short_wait
extern session_status
extern session_timestamp
extern session_wait_mode
%else
ORG 0xf070
%define session_carrier_present 0x4861
%define session_delay_ticks 0x6b98
%define session_local_cancel 0x3f4b
%define session_queued_count 0x8e20
%define session_short_wait 0x203e
%define session_status 0xe498
%define session_timestamp 0xf0d4
%define session_wait_mode 0x3986
%endif
%include "encodings.inc"
session_wait: push di
session_at_f071: push si
session_at_f072: sub_load si,si
session_at_f074: cmp [session_short_wait],si
session_at_f078: jz short session_at_f080
session_at_f07a: mov di,0x5b
session_at_f07d: jmp short session_at_f08f
session_at_f07f: nop
session_at_f080: cmp word [session_wait_mode],0x1
session_at_f085: sbb_load di,di
session_at_f087: and di,0xff5c
session_at_f08b: add di,0xc8
session_at_f08f: or_load di,di
session_at_f091: jng short session_at_f0a6
session_at_f093: mov ax,0x1
session_at_f096: push ax
session_at_f097: call session_delay_ticks
session_at_f09a: cmp word [session_queued_count],0x0
session_at_f09f: jnz short session_at_f0b2
session_at_f0a1: inc si
session_at_f0a2: cmp_load si,di
session_at_f0a4: jl short session_at_f093
session_at_f0a6: call session_local_cancel
session_at_f0a9: or_load ax,ax
session_at_f0ab: jz short session_at_f0bc
session_at_f0ad: mov ax,0xb
session_at_f0b0: jmp short session_at_f0c6
session_at_f0b2: call session_timestamp
session_at_f0b5: mov ax,0x1
session_at_f0b8: pop si
session_at_f0b9: pop di
session_at_f0ba: ret
session_at_f0bb: nop
session_at_f0bc: call session_carrier_present
session_at_f0bf: or_load ax,ax
session_at_f0c1: jnz short session_at_f0d0
session_at_f0c3: mov ax,0xf
session_at_f0c6: push ax
session_at_f0c7: call session_status
session_at_f0ca: add sp,0x2
session_at_f0cd: mov ax,0xffff
session_at_f0d0: pop si
session_at_f0d1: pop di
session_at_f0d2: ret
