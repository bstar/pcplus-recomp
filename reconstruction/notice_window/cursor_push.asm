; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_cursor_push
extern window_cursor_get
extern window_state_7a36
extern window_state_7a4c
%define short
%else
ORG 27482
%define window_cursor_get 31118
%define window_state_7a36 31286
%define window_state_7a4c 31308
%endif
%include "encodings.inc"
window_cursor_push:
L_6b5a: call window_cursor_get
L_6b5d: mov bx,[window_state_7a36]
L_6b61: mov [bx],ax
L_6b63: cmp bx,window_state_7a4c
L_6b67: jnc short L_6b6c
L_6b69: add bx,0x2
L_6b6c: mov [window_state_7a36],bx
L_6b70: ret
