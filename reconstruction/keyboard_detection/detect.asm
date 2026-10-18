; Exact PCPlus2.01 resident7916..793a: select enhanced keyboard BIOS iff BDA bit.
BITS 16
CPU 8086
%ifdef KEYBOARD_DETECTION_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_select_bios_original,keyboard_detect_bios_mode
extern keyboard_bios_mode
%else
ORG 0x7916
%define keyboard_bios_mode 0x7ac0
%endif
%include "encodings.inc"
; Original callee-clean word:0=>standard; nonzero=>AUTO (NOT forcedenhanced).
; BX/DX/ES/AX/flags scratch; AX unspecified for arg0,0/1 for AUTO.
keyboard_select_bios_original:
 mov_load bx,sp
 mov dx,[bx+2]
 mov byte [keyboard_bios_mode],0
 cmp dx,0
 je short .done
 xor_load ax,ax
 mov es,ax
 test byte [es:0x0496],0x10
 je short .done
 inc ax
 mov byte [keyboard_bios_mode],0x10
.done:
 ret 2
%ifdef KEYBOARD_DETECTION_OMF
; Maintained noarg near wrapper: returns fullAX0/10h and updates BIOSmode.
; Preserve BX/CX/DX/ES/BP/SI/DI/DS; no INT16 or port IO. DS=SS ABI.
keyboard_detect_bios_mode:
 push bx
 push dx
 push es
 mov ax,1
 push ax
 call keyboard_select_bios_original
 xor ax,ax
 mov al,[keyboard_bios_mode]
 pop es
 pop dx
 pop bx
 ret
%endif
