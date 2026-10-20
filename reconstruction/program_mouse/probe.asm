; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _TEXT public class=CODE use16
global mouse_probe
%define short
%else
ORG 30388
%endif
%include "encodings.inc"
mouse_probe:
L_76b4: push bp
L_76b5: mov_load bp,sp
L_76b7: mov ax,0x3533
L_76ba: int byte 0x21
L_76bc: mov ax,es
L_76be: or_load ax,bx
L_76c0: jz short L_76e4
L_76c2: cmp word [bp+0x4],0x0
L_76c6: jnz short L_76ce
L_76c8: xor_load ax,ax
L_76ca: int byte 0x33
L_76cc: jmp short L_76e4
L_76ce: mov ax,0x21
L_76d1: int byte 0x33
L_76d3: cmp ax,strict word 0xffff
L_76d6: jnz short L_76e2
L_76d8: cmp bx,0x1
L_76db: jc short L_76e2
L_76dd: cmp bx,0x3
L_76e0: jna short L_76e4
L_76e2: xor_load ax,ax
L_76e4: pop bp
L_76e5: ret word 0x2
