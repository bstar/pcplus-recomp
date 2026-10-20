; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_text
extern display_cell_offset
extern display_snow_disable
extern display_snow_enable
extern display_segment
%define short
%else
ORG 27632
%define display_cell_offset 32258
%define display_snow_disable 30654
%define display_snow_enable 30638
%define display_segment 31352
%endif
%include "encodings.inc"
display_text:
L_6bf0: push bp
L_6bf1: mov_load bp,sp
L_6bf3: push di
L_6bf4: push si
L_6bf5: mov dx,[bp+0x8]
L_6bf8: call display_cell_offset
L_6bfb: mov_load di,ax
L_6bfd: push di
L_6bfe: mov es,word [display_segment]
L_6c02: call display_snow_disable
L_6c05: mov si,[bp+0x4]
L_6c08: mov ax,[bp+0x6]
L_6c0b: mov_load ah,al
L_6c0d: lodsb
L_6c0e: or_load al,al
L_6c10: jz short L_6c15
L_6c12: stosw
L_6c13: jmp short L_6c0d
L_6c15: call display_snow_enable
L_6c18: pop di
L_6c19: pop si
L_6c1a: pop di
L_6c1b: pop bp
L_6c1c: ret word 0x6
