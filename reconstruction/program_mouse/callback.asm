; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global mouse_callback
global mouse_depth
%define mouse_group DGROUP
extern mouse_events
extern mouse_flags
extern mouse_motion_y
extern mouse_motion_x
%define short
%else
ORG 32882
%define mouse_events 32922
%define mouse_flags 31318
%define mouse_motion_y 31322
%define mouse_motion_x 31320
%define mouse_group 0xfb7
%endif
%include "encodings.inc"
mouse_depth: dw 0xffff
mouse_callback:
L_8074: cli
L_8075: inc word [cs:mouse_depth]
L_807a: jnz short L_8092
L_807c: sti
L_807d: push ds
L_807e: mov bx,mouse_group
L_8081: mov ds,bx
L_8083: mov [mouse_flags],ax
L_8086: mov [mouse_motion_y],di
L_808a: mov [mouse_motion_x],si
L_808e: call mouse_events
L_8091: pop ds
L_8092: cli
L_8093: dec word [cs:mouse_depth]
L_8098: retf
