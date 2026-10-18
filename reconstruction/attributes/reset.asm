; Recovered PCPlus 2.01 attribute instructions; see docs/ATTRIBUTES.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTES_OMF
SEGMENT _TEXT public class=CODE use16
global attributes_reset
extern attributes_current
extern attributes_normal_value
%define short
%else
ORG 0x24da
%define attributes_current 0x1f70
%define attributes_normal_value 0x1d32
%endif
%include "encodings.inc"
attributes_reset:
L_24da: mov ax,[attributes_normal_value]
L_24dd: mov [attributes_current],ax
L_24e0: ret
