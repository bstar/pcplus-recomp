; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_fill
extern display_snow_cell
extern display_segment
extern display_status_port
%define short
%else
ORG 27680
%define display_snow_cell 32288
%define display_segment 31352
%define display_status_port 31374
%endif
%include "encodings.inc"
display_fill:
L_6c20: mov_load bx,sp
L_6c22: push di
L_6c23: mov cx,[bx+0x2]
L_6c26: mov di,[bx+0x4]
L_6c29: mov ax,[bx+0x6]
L_6c2c: xchg al,ah
L_6c2e: mov es,word [display_segment]
L_6c32: mov dx,[display_status_port]
L_6c36: cmp dx,0x0
L_6c39: jnz short L_6c41
L_6c3b: rep stosw
L_6c3d: pop di
L_6c3e: ret word 0x6
L_6c41: jcxz L_6c3d
L_6c43: call display_snow_cell
L_6c46: loop L_6c43
L_6c48: jmp short L_6c3d
