; Owned ASPECT BIOS selection over the recovered acquisition component.
; No private application queue, no second foreground reader. DS=SS.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern keyboard_bios_read,keyboard_bios_peek,keyboard_detect_bios_mode
global _runtime_keyboard_read,_runtime_keyboard_peek,_runtime_keyboard_auto
_runtime_keyboard_read: jmp keyboard_bios_read
_runtime_keyboard_peek: jmp keyboard_bios_peek
_runtime_keyboard_auto:
 mov word [_runtime_keyboard_mode],0
 jmp keyboard_detect_bios_mode
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global _runtime_keyboard_mode,keyboard_bios_mode
_runtime_keyboard_mode:
keyboard_bios_mode: dw 0
