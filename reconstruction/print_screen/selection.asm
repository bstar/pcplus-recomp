; Exact original screen-printer instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINT_SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global print_selection_original
global print_at_e3cf
global print_at_e3d1
global print_at_e3d4
global print_at_e3d6
global print_at_e3d9
global print_at_e3da
global print_at_e3dd
global print_at_e3e0
global print_at_e3e5
global print_at_e3e7
global print_at_e3ea
global print_at_e3eb
global print_at_e3ee
global print_at_e3f1
extern printer_byte_original
extern print_formfeed
extern print_region_mode
extern print_screen_original
%else
ORG 0xe3ca
%define printer_byte_original 0x36fc
%define print_formfeed 0x3980
%define print_region_mode 0x3982
%define print_screen_original 0xe2f8
%endif
%include "encodings.inc"
print_selection_original: cmp word [print_region_mode],0x0
print_at_e3cf: jz short print_at_e3d6
print_at_e3d1: mov ax,0x2
print_at_e3d4: jmp short print_at_e3d9
print_at_e3d6: mov ax,0x1
print_at_e3d9: push ax
print_at_e3da: call print_screen_original
print_at_e3dd: add sp,0x2
print_at_e3e0: cmp word [print_formfeed],0x0
print_at_e3e5: jz short print_at_e3f1
print_at_e3e7: mov ax,0xc
print_at_e3ea: push ax
print_at_e3eb: call printer_byte_original
print_at_e3ee: add sp,0x2
print_at_e3f1: ret
