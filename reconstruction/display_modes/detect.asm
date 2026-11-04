; Exact PCPlus2.01 capability probe. Counters must be initialized by its owner.
BITS 16
CPU 8086
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_detect
extern display_virtual_buffer,display_font_capable,display_scanline_capable
extern display_extended_mode,display_geometry
%define short
%else
ORG 0x6cd8
%define display_virtual_buffer 0x7e34
%define display_font_capable 0x7a6e
%define display_scanline_capable 0x7a70
%define display_extended_mode 0x7a68
%define display_geometry 0x6d1a
%endif
display_detect:
 mov ah,0x0f
 int 0x10
 cmp al,7
 je short .mono
.probe:
 call display_virtual_buffer
 mov ah,0x12
 mov bx,0xab10
 int 0x10
 cmp bh,0xab
 je short .vendor
 inc word [display_font_capable]
 mov ax,0x1a00
 int 0x10
 cmp al,0x1a
 jne short .vendor
 inc word [display_scanline_capable]
.vendor:
 mov ax,0x6f00
 int 0x10
 cmp bx,0x5637
 jne short .done
 cmp word [display_scanline_capable],0
 je short .done
 inc word [display_extended_mode]
.done:
 jmp short display_geometry
.mono:
 jmp short .probe
