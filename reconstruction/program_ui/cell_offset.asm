; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_cell_offset
extern display_columns
%define short
%else
ORG 32258
%define display_columns 31346
%endif
%include "encodings.inc"
display_cell_offset:
L_7e02: mov al,[display_columns]
L_7e05: mul dh
L_7e07: xor_load dh,dh
L_7e09: add_load ax,dx
L_7e0b: shl ax,1
L_7e0d: ret
