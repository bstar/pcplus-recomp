; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_attribute
extern window_state_7a78
extern window_state_7a8e
%define short
%else
ORG 27780
%define window_state_7a78 31352
%define window_state_7a8e 31374
%endif
%include "encodings.inc"
window_attribute:
L_6c84: mov_load bx,sp
L_6c86: mov_load cx,di
L_6c88: mov di,[bx+0x2]
L_6c8b: mov ax,[bx+0x4]
L_6c8e: mov es,word [window_state_7a78]
L_6c92: mov dx,[window_state_7a8e]
L_6c96: cmp dx,0x0
L_6c99: jnz short L_6ca1
L_6c9b: stosb
L_6c9c: mov_load di,cx
L_6c9e: ret word 0x4
L_6ca1: mov_load bl,al
L_6ca3: in al,dx
L_6ca4: test al,0x1
L_6ca6: jnz short L_6ca3
L_6ca8: cli
L_6ca9: in al,dx
L_6caa: test al,0x1
L_6cac: jz short L_6ca9
L_6cae: xchg ax,bx
L_6caf: stosb
L_6cb0: sti
L_6cb1: jmp short L_6c9c
