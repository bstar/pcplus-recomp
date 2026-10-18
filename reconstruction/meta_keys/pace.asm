; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_pace
extern meta_pace_counter
extern meta_pace_calibration
%define short
%else
ORG 0x6b72
%define meta_pace_counter 0x7a4e
%define meta_pace_calibration 0x7ac4
%endif
%include "encodings.inc"
meta_keys_pace:
L_6b72: mov_load bx,sp
L_6b74: mov dx,[bx+0x2]
L_6b77: cmp dx,0x0
L_6b7a: jz short L_6b95
L_6b7c: mov ax,ds
L_6b7e: mov es,ax
L_6b80: mov bx,meta_pace_counter
L_6b83: mov cx,[meta_pace_calibration]
L_6b87: sub cx,0x1
L_6b8a: adc ax,strict word 0x0
L_6b8d: cmp cx,[es:bx]
L_6b90: jnz short L_6b87
L_6b92: dec dx
L_6b93: jnz short L_6b83
L_6b95: ret word 0x2
