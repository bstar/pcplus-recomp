; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_stride
extern window_snow_cell
extern window_state_7a78
extern window_state_7a8e
extern window_state_7a7a
%define short
%else
ORG 32820
%define window_snow_cell 32288
%define window_state_7a78 31352
%define window_state_7a8e 31374
%define window_state_7a7a 31354
%endif
%include "encodings.inc"
window_stride:
L_8034: mov_load bx,sp
L_8036: push di
L_8037: mov cx,[bx+0x2]
L_803a: jcxz L_805d
L_803c: mov di,[bx+0x4]
L_803f: mov ax,[bx+0x6]
L_8042: xchg al,ah
L_8044: mov es,word [window_state_7a78]
L_8048: mov dx,[window_state_7a8e]
L_804c: cmp dx,0x0
L_804f: jnz short L_8061
L_8051: mov dx,[window_state_7a7a]
L_8055: sub dx,0x2
L_8058: stosw
L_8059: add_load di,dx
L_805b: loop L_8058
L_805d: pop di
L_805e: ret word 0x6
L_8061: mov bx,[window_state_7a7a]
L_8065: sub bx,0x2
L_8068: call window_snow_cell
L_806b: add_load di,bx
L_806d: loop L_8068
L_806f: jmp short L_805d
