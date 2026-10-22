; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_cursor_pop
extern window_cursor
extern window_state_7a36
extern window_state_7a38
%define short
%else
ORG 27458
%define window_cursor 28280
%define window_state_7a36 31286
%define window_state_7a38 31288
%endif
%include "encodings.inc"
window_cursor_pop:
L_6b42: mov bx,[window_state_7a36]
L_6b46: cmp bx,[window_state_7a38]
L_6b4a: jz short L_6b4f
L_6b4c: sub bx,0x2
L_6b4f: mov [window_state_7a36],bx
L_6b53: push word [bx]
L_6b55: call window_cursor
L_6b58: ret
