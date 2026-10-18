BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern keyboard_detect_bios_mode,keyboard_select_bios_original
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 xor ax,ax
 mov es,ax
 xor bx,bx
 test byte [es:0x496],0x10
 jz .expected
 mov bx,0x10
.expected:
 mov [expected_mode],bx
 call keyboard_detect_bios_mode
 cmp ax,[expected_mode]
 jne .fail
 cmp al,[keyboard_bios_mode]
 jne .fail
 xor ax,ax
 push ax
 call keyboard_select_bios_original
 cmp byte [keyboard_bios_mode],0
 jne .fail
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
global keyboard_detection_test_standard
keyboard_detection_test_standard:
 xor ax,ax
 push ax
 call keyboard_select_bios_original
 ret
SEGMENT _DATA public class=DATA use16
global keyboard_bios_mode
keyboard_bios_mode: db 0x55
expected_mode: dw 0
SEGMENT STACK stack class=STACK use16
 resb 2048
stack_top:
