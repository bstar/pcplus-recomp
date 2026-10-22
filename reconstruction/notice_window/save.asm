; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_save
extern window_cursor_push
extern window_cursor
extern window_snapshot
extern window_alert
extern window_sound_open
extern window_expand
extern window_state_1d3e
extern window_state_3352
%define short
%else
ORG 16327
%define window_cursor_push 27482
%define window_cursor 28280
%define window_snapshot 27582
%define window_alert 18575
%define window_sound_open 30554
%define window_expand 28808
%define window_state_1d3e 7486
%define window_state_3352 13138
%endif
%include "encodings.inc"
window_save:
L_3fc7: push bp
L_3fc8: mov_load bp,sp
L_3fca: sub sp,0x4
L_3fcd: push di
L_3fce: call window_cursor_push
L_3fd1: mov ax,0x64c8
L_3fd4: push ax
L_3fd5: call window_cursor
L_3fd8: call window_snapshot
L_3fdb: mov_load di,ax
L_3fdd: mov [bp-0x2],dx
L_3fe0: or_load dx,ax
L_3fe2: jnz short L_3fe7
L_3fe4: call window_alert
L_3fe7: cmp word [window_state_1d3e],0x0
L_3fec: jz short L_3ff1
L_3fee: call window_sound_open
L_3ff1: mov bx,[bp+0x4]
L_3ff4: push word [bx]
L_3ff6: push word [bx+0x2]
L_3ff9: push word [bx+0x4]
L_3ffc: push word [bx+0x6]
L_3fff: mov bx,[bx+0x8]
L_4002: push word [bx]
L_4004: push word [window_state_3352]
L_4008: call window_expand
L_400b: mov_load ax,di
L_400d: mov dx,[bp-0x2]
L_4010: pop di
L_4011: mov_load sp,bp
L_4013: pop bp
L_4014: ret
