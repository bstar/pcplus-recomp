; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_snow_cell
%define short
%else
ORG 32288
%endif
%include "encodings.inc"
display_snow_cell:
L_7e20: push bx
L_7e21: mov_load bx,ax
L_7e23: in al,dx
L_7e24: test al,0x1
L_7e26: jnz short L_7e23
L_7e28: cli
L_7e29: in al,dx
L_7e2a: test al,0x1
L_7e2c: jz short L_7e29
L_7e2e: xchg ax,bx
L_7e2f: stosw
L_7e30: sti
L_7e31: pop bx
L_7e32: ret
