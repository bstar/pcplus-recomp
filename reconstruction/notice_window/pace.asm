; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_pace
extern window_state_7a4e
extern window_state_7ac4
%define short
%else
ORG 27506
%define window_state_7a4e 31310
%define window_state_7ac4 31428
%endif
%include "encodings.inc"
window_pace:
L_6b72: mov_load bx,sp
L_6b74: mov dx,[bx+0x2]
L_6b77: cmp dx,0x0
L_6b7a: jz short L_6b95
L_6b7c: mov ax,ds
L_6b7e: mov es,ax
L_6b80: mov bx,window_state_7a4e
L_6b83: mov cx,[window_state_7ac4]
L_6b87: sub cx,0x1
L_6b8a: adc ax,strict word 0x0
L_6b8d: cmp cx,[es:bx]
L_6b90: jnz short L_6b87
L_6b92: dec dx
L_6b93: jnz short L_6b83
L_6b95: ret word 0x2
