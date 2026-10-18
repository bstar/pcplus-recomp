; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_ignore_control
%define short
%else
ORG 0xe60
%endif
%include "encodings.inc"
terminal_ignore_control:
L_0e60: ret
