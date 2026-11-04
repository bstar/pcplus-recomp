; Exact PCPlus2.01 AH=FEh display-buffer probe, not an allocation service.
BITS 16
CPU 8086
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_virtual_buffer
extern display_segment,display_legacy
%else
ORG 0x7e34
%define display_segment 0x7a78
%define display_legacy 0x7a66
%endif
display_virtual_buffer:
 push di
 mov es,[display_segment]
 mov di,strict word 0
 mov ah,0xfe
 int 0x10
 mov ax,es
 cmp ax,[display_segment]
 jne short .changed
 mov ax,strict word 0
.commit:
 mov [display_legacy],ax
 pop di
 ret
.changed:
 mov [display_segment],ax
 mov ax,strict word 1
 jmp short .commit
