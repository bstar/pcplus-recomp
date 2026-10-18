; Maintained near-call wrappers for recovered callee-cleanup normalization.
; DS must equal SS, as in the recovered stack-argument routines.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern keyboard_normalize_bios,keyboard_normalize_extended
global keyboard_key_from_bios,keyboard_key_for_extended
keyboard_key_from_bios:
 mov bx,sp
 push word [bx+2]
 call keyboard_normalize_bios
 ret
keyboard_key_for_extended:
 mov bx,sp
 push word [bx+2]
 call keyboard_normalize_extended
 ret
