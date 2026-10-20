; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_snow_disable
extern display_status_port
%define short
%else
ORG 30654
%define display_status_port 31374
%endif
%include "encodings.inc"
display_snow_disable:
L_77be: mov dx,[display_status_port]
L_77c2: cmp dx,0x0
L_77c5: jz short L_77d1
L_77c7: in al,dx
L_77c8: test al,0x8
L_77ca: jz short L_77c7
L_77cc: mov al,0x25
L_77ce: mov dl,0xd8
L_77d0: out dx,al
L_77d1: ret
