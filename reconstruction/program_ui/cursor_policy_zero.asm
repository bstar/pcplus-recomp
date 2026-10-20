; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_cursor_policy_zero
extern display_cursor_shape
extern display_cursor_policy
%define short
%else
ORG 28250
%define display_cursor_shape 32344
%define display_cursor_policy 31340
%endif
%include "encodings.inc"
display_cursor_policy_zero:
L_6e5a: mov word [display_cursor_policy],0x0
L_6e60: mov bx,0x1
L_6e63: jmp near display_cursor_shape
