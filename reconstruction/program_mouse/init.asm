; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _TEXT public class=CODE use16
global mouse_init
extern mouse_probe
extern mouse_bind
extern mouse_present
extern mouse_scale_y
extern mouse_scale_x
extern mouse_flags
%define short
%else
ORG 30442
%define mouse_probe 30388
%define mouse_bind 32658
%define mouse_present 31316
%define mouse_scale_y 31314
%define mouse_scale_x 31312
%define mouse_flags 31318
%endif
%include "encodings.inc"
mouse_init:
L_76ea: push bp
L_76eb: mov_load bp,sp
L_76ed: push word [bp+0x8]
L_76f0: call mouse_probe
L_76f3: mov [mouse_present],ax
L_76f6: cmp ax,strict word 0x0
L_76f9: jz short L_771e
L_76fb: mov ax,0xb
L_76fe: int byte 0x33
L_7700: mov ax,[bp+0x4]
L_7703: mov [mouse_scale_y],ax
L_7706: mov ax,[bp+0x6]
L_7709: mov [mouse_scale_x],ax
L_770c: mov cx,0x8
L_770f: mov bx,mouse_flags
L_7712: xor_load ax,ax
L_7714: mov [bx],ax
L_7716: add bx,0x2
L_7719: loop L_7714
L_771b: call mouse_bind
L_771e: pop bp
L_771f: ret word 0x6
