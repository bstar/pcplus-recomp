; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_snow_enable
extern display_status_port
%define short
%else
ORG 30638
%define display_status_port 31374
%endif
%include "encodings.inc"
display_snow_enable:
L_77ae: mov dx,[display_status_port]
L_77b2: cmp dx,0x0
L_77b5: jz short L_77bc
L_77b7: mov al,0x2d
L_77b9: mov dl,0xd8
L_77bb: out dx,al
L_77bc: ret
