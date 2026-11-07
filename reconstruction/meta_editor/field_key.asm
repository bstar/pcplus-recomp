; Recovered 2.01 Meta Keys component; external UI boundaries remain explicit.
BITS 16
CPU 8086
%ifdef META_EDITOR_OMF
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
global meta_editor_field_key
%else
ORG 57953
%endif
%include "encodings.inc"
meta_editor_field_key:
L_e261: push bp
L_e262: mov_load bp,sp
L_e264: push si
L_e265: mov si,[bp+0x4]
L_e268: mov dx,[si]
L_e26a: mov_load ax,dx
L_e26c: sub ax,strict word 0x9
L_e26f: jz short L_e284
L_e271: sub ax,strict word 0x4
L_e274: jz short L_e280
L_e276: sub ax,0xf2
L_e279: jz short L_e28c
L_e27b: sub ax,0xe01
L_e27e: jz short L_e284
L_e280: sub_load ax,ax
L_e282: jmp short L_e28f
L_e284: mov word [si],0xd
L_e288: mov_load ax,dx
L_e28a: jmp short L_e28f
L_e28c: mov ax,0xff9d
L_e28f: pop si
L_e290: mov_load sp,bp
L_e292: pop bp
L_e293: ret
%ifdef META_EDITOR_OMF
SEGMENT _DATA public class=DATA use16
%endif
