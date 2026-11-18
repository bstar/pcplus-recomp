; Recovered overlay16 DA1C: one non-consuming peek, original RET2 normalizer.
BITS 16
CPU 8086
%ifdef ASPECT_HITKEY_FLAT
ORG 0xda1c
%define keyboard_peek 0x651a
%define keyboard_normalize_bios 0x77d2
%else
SEGMENT _TEXT public class=CODE use16
global aspect_hitkey_native,_aspect_hitkey_native
extern keyboard_normalize_bios
%ifdef ASPECT_HITKEY_NATIVE_PARENT
extern keyboard_peek
%elifdef ASPECT_HITKEY_DIAGNOSTIC
%define keyboard_peek _runtime_hitkey_peek
extern _runtime_hitkey_peek
%else
; A standalone interpreter has no application mouse queue. Its actual owned
; BIOS peek uses the recovered standard/enhanced selection and empty/ZF rules.
%define keyboard_peek _runtime_keyboard_peek
extern _runtime_keyboard_peek
%endif
_aspect_hitkey_native:
%endif
aspect_hitkey_native:
 call keyboard_peek
 push ax
 call keyboard_normalize_bios
 ret
%ifdef ASPECT_HITKEY_NATIVE_PARENT
global terminal_hitkey_sample
terminal_hitkey_sample:
 call aspect_hitkey_native
 retf
%endif
