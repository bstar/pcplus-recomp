; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_write
extern window_snow_cell
extern window_state_7a78
extern window_state_7a8e
%define short
%else
ORG 27828
%define window_snow_cell 32288
%define window_state_7a78 31352
%define window_state_7a8e 31374
%endif
%include "encodings.inc"
window_write:
L_6cb4: mov_load bx,sp
L_6cb6: mov_load cx,di
L_6cb8: mov di,[bx+0x2]
L_6cbb: mov ax,[bx+0x4]
L_6cbe: xchg al,ah
L_6cc0: mov es,word [window_state_7a78]
L_6cc4: mov dx,[window_state_7a8e]
L_6cc8: cmp dx,0x0
L_6ccb: jnz short L_6cd3
L_6ccd: stosw
L_6cce: mov_load di,cx
L_6cd0: ret word 0x4
L_6cd3: call window_snow_cell
L_6cd6: jmp short L_6cce
