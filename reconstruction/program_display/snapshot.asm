; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_snapshot
extern display_allocate
extern display_snow_disable
extern display_snow_enable
extern display_bytes
extern display_segment
%define short
%else
ORG 27582
%define display_allocate 34319
%define display_snow_disable 30654
%define display_snow_enable 30638
%define display_bytes 31356
%define display_segment 31352
%endif
%include "encodings.inc"
display_snapshot:
L_6bbe: push di
L_6bbf: push si
L_6bc0: mov si,[display_bytes]
L_6bc4: push si
L_6bc5: call display_allocate
L_6bc8: add sp,0x2
L_6bcb: mov_load bx,ax
L_6bcd: or_load bx,dx
L_6bcf: jz short L_6bed
L_6bd1: mov es,dx
L_6bd3: mov_load di,ax
L_6bd5: push ax
L_6bd6: call display_snow_disable
L_6bd9: mov_load cx,si
L_6bdb: shr cx,1
L_6bdd: push ds
L_6bde: mov ds,word [display_segment]
L_6be2: xor_load si,si
L_6be4: rep movsw
L_6be6: pop ds
L_6be7: call display_snow_enable
L_6bea: mov dx,es
L_6bec: pop ax
L_6bed: pop si
L_6bee: pop di
L_6bef: ret
