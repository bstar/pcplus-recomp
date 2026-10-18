; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_default_attribute
extern screen_attributes_base
extern erase_attribute_values_base
extern csi_erase_attribute
%define short
%else
ORG 0x2d38
%define screen_attributes_base 0x39c4
%define erase_attribute_values_base 0x39c2
%define csi_erase_attribute 0xd008
%endif
%include "encodings.inc"
erase_default_attribute:
L_2d38: mov bx,[screen_attributes_base]
L_2d3c: test byte [bx],0x80
L_2d3f: jz short L_2d48
L_2d41: mov bx,[erase_attribute_values_base]
L_2d45: mov al,[bx]
L_2d47: ret
L_2d48: mov al,[csi_erase_attribute]
L_2d4b: ret
