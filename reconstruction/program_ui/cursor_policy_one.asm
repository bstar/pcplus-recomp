; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_cursor_policy_one
extern display_cursor_shape
extern display_cursor_policy
%define short
%else
ORG 28106
%define display_cursor_shape 32344
%define display_cursor_policy 31340
%endif
%include "encodings.inc"
display_cursor_policy_one:
L_6dca: cmp word [display_cursor_policy],0x1
L_6dcf: jg short L_6ddc
L_6dd1: mov word [display_cursor_policy],0x1
L_6dd7: xor_load bx,bx
L_6dd9: jmp near display_cursor_shape
L_6ddc: ret
