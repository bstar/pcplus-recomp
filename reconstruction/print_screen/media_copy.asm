; Exact original screen-printer instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINT_SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global print_media_copy_original
global print_at_e085
global print_at_e087
global print_at_e088
global print_at_e089
global print_at_e08e
global print_at_e090
global print_at_e093
global print_at_e095
global print_at_e099
global print_at_e09b
global print_at_e09e
global print_at_e0a0
global print_at_e0a2
global print_at_e0a4
global print_at_e0a5
global print_at_e0a7
global print_at_e0aa
global print_at_e0ac
global print_at_e0ad
global print_at_e0af
global print_at_e0b1
global print_at_e0b2
global print_at_e0b5
global print_at_e0b7
global print_at_e0b8
global print_at_e0bb
global print_at_e0bc
global print_at_e0bf
global print_at_e0c2
global print_at_e0c4
global print_at_e0c9
global print_at_e0cb
global print_at_e0d1
global print_at_e0d4
global print_at_e0d6
global print_at_e0db
global print_at_e0dd
global print_at_e0e3
global print_at_e0e5
global print_at_e0e6
global print_at_e0e9
global print_at_e0ea
global print_at_e0eb
global print_at_e0ec
global print_at_e0f0
global print_at_e0f2
global print_at_e0f3
global print_at_e0f4
global print_at_e0f6
global print_at_e0f7
extern printer_toggle_original
extern printer_enabled
extern print_parameters
extern print_parameter_count
extern print_copy_policy
extern print_copy_fallback
extern print_screen_original
extern print_selection_original
%else
ORG 0xe084
%define printer_toggle_original 0x1a76
%define printer_enabled 0x3988
%define print_parameters 0xcb3c
%define print_parameter_count 0xcb5c
%define print_copy_policy 0xceac
%define print_copy_fallback 0xd0d0
%define print_screen_original 0xe2f8
%define print_selection_original 0xe3ca
%endif
%include "encodings.inc"
print_media_copy_original: push bp
print_at_e085: mov_load bp,sp
print_at_e087: push di
print_at_e088: push si
print_at_e089: cmp word [print_parameter_count],0x0
print_at_e08e: jnz short print_at_e093
print_at_e090: call print_selection_original
print_at_e093: sub_load di,di
print_at_e095: cmp [print_parameter_count],di
print_at_e099: jng short print_at_e0f2
print_at_e09b: mov si,print_parameters
print_at_e09e: mov ax,[si]
print_at_e0a0: or_load ax,ax
print_at_e0a2: jz short print_at_e0b2
print_at_e0a4: dec ax
print_at_e0a5: jz short print_at_e0b8
print_at_e0a7: sub ax,strict word 0x3
print_at_e0aa: jz short print_at_e0c4
print_at_e0ac: dec ax
print_at_e0ad: jz short print_at_e0d6
print_at_e0af: jmp short print_at_e0e9
print_at_e0b1: nop
print_at_e0b2: call print_selection_original
print_at_e0b5: jmp short print_at_e0e9
print_at_e0b7: nop
print_at_e0b8: mov ax,0x3
print_at_e0bb: push ax
print_at_e0bc: call print_screen_original
print_at_e0bf: add sp,0x2
print_at_e0c2: jmp short print_at_e0e9
print_at_e0c4: cmp word [print_copy_policy],0x0
print_at_e0c9: jz short print_at_e0e9
print_at_e0cb: mov word [printer_enabled],0x1
print_at_e0d1: call printer_toggle_original
print_at_e0d4: jmp short print_at_e0e9
print_at_e0d6: cmp word [print_copy_policy],0x0
print_at_e0db: jz short print_at_e0e6
print_at_e0dd: mov word [printer_enabled],0x0
print_at_e0e3: jmp short print_at_e0d1
print_at_e0e5: nop
print_at_e0e6: call print_copy_fallback
print_at_e0e9: inc si
print_at_e0ea: inc si
print_at_e0eb: inc di
print_at_e0ec: cmp [print_parameter_count],di
print_at_e0f0: jg short print_at_e09e
print_at_e0f2: pop si
print_at_e0f3: pop di
print_at_e0f4: mov_load sp,bp
print_at_e0f6: pop bp
print_at_e0f7: ret
