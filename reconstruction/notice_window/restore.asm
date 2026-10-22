; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_restore
extern window_alert
extern window_cursor
extern window_sound_close
extern window_collapse
extern window_cursor_pop
extern window_state_1d3e
%define short
%else
ORG 16405
%define window_alert 18575
%define window_cursor 28280
%define window_sound_close 30564
%define window_collapse 29486
%define window_cursor_pop 27458
%define window_state_1d3e 7486
%endif
%include "encodings.inc"
window_restore:
L_4015: push bp
L_4016: mov_load bp,sp
L_4018: push di
L_4019: mov di,[bp+0x6]
L_401c: mov ax,[bp+0x8]
L_401f: or_load ax,di
L_4021: jnz short L_4028
L_4023: call window_alert
L_4026: jmp short L_404e
L_4028: mov ax,0x64c8
L_402b: push ax
L_402c: call window_cursor
L_402f: cmp word [window_state_1d3e],0x0
L_4034: jz short L_4039
L_4036: call window_sound_close
L_4039: mov bx,[bp+0x4]
L_403c: push word [bx]
L_403e: push word [bx+0x2]
L_4041: push word [bx+0x4]
L_4044: push word [bx+0x6]
L_4047: push word [bp+0x8]
L_404a: push di
L_404b: call window_collapse
L_404e: call window_cursor_pop
L_4051: pop di
L_4052: mov_load sp,bp
L_4054: pop bp
L_4055: ret
