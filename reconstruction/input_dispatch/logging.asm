; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_log_character
extern terminal_sink_36fc
extern terminal_sink_8436
extern terminal_sink_427f
extern terminal_sink_bb23
extern screen_viewport_refresh
extern terminal_sink_3988_enabled
extern terminal_cr_adds_lf
extern terminal_sink_398a_enabled
extern terminal_sink_398c_disabled
extern terminal_sink_handle
extern terminal_sink_error_state
%define short
%else
ORG 0x9b6
%define terminal_sink_36fc 0x36fc
%define terminal_sink_8436 0x8436
%define terminal_sink_427f 0x427f
%define terminal_sink_bb23 0xbb23
%define screen_viewport_refresh 0x2fb8
%define terminal_sink_3988_enabled 0x3988
%define terminal_cr_adds_lf 0x1d24
%define terminal_sink_398a_enabled 0x398a
%define terminal_sink_398c_disabled 0x398c
%define terminal_sink_handle 0xd114
%define terminal_sink_error_state 0x418a
%endif
%include "encodings.inc"
terminal_log_character:
L_09b6: push bp
L_09b7: mov_load bp,sp
L_09b9: push si
L_09ba: mov si,[bp+0x4]
L_09bd: cmp si,0xff
L_09c1: jz short L_0a35
L_09c3: cmp si,0x7f
L_09c6: jz short L_0a35
L_09c8: cmp word [terminal_sink_3988_enabled],0x0
L_09cd: jz short L_09ec
L_09cf: push si
L_09d0: call terminal_sink_36fc
L_09d3: add sp,0x2
L_09d6: cmp si,0xd
L_09d9: jnz short L_09ec
L_09db: cmp word [terminal_cr_adds_lf],0x0
L_09e0: jz short L_09ec
L_09e2: mov ax,0xa
L_09e5: push ax
L_09e6: call terminal_sink_36fc
L_09e9: add sp,0x2
L_09ec: cmp word [terminal_sink_398a_enabled],0x0
L_09f1: jz short L_0a35
L_09f3: cmp word [terminal_sink_398c_disabled],0x0
L_09f8: jnz short L_0a35
L_09fa: cmp si,0xd
L_09fd: jnz short L_0a1a
L_09ff: cmp word [terminal_cr_adds_lf],0x0
L_0a04: jz short L_0a35
L_0a06: push word [terminal_sink_handle]
L_0a0a: mov ax,0xa
L_0a0d: push ax
L_0a0e: call terminal_sink_8436
L_0a11: add sp,0x4
L_0a14: pop si
L_0a15: mov_load sp,bp
L_0a17: pop bp
L_0a18: ret
L_0a19: nop
L_0a1a: push word [terminal_sink_handle]
L_0a1e: push si
L_0a1f: call terminal_sink_8436
L_0a22: add sp,0x4
L_0a25: inc ax
L_0a26: jnz short L_0a35
L_0a28: mov bx,[terminal_sink_error_state]
L_0a2c: call terminal_sink_427f
L_0a2f: call terminal_sink_bb23
L_0a32: call screen_viewport_refresh
L_0a35: pop si
L_0a36: mov_load sp,bp
L_0a38: pop bp
L_0a39: ret
