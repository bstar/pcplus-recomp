; Recovered PCPlus 2.01 scroll instructions; see docs/SCROLL.md.
BITS 16
CPU 8086
%ifdef SCROLL_OMF
SEGMENT _TEXT public class=CODE use16
global screen_wrap_forward
extern screen_linefeed
extern screen_cursor_column
%define short
%else
ORG 0x12c8
%define screen_linefeed 0x1d88
%define screen_cursor_column 0x399e
%endif
%include "encodings.inc"
screen_wrap_forward:
L_12c8: mov word [screen_cursor_column],0x0
L_12ce: jmp near screen_linefeed
