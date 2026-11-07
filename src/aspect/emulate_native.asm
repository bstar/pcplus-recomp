; Native opcode2F owner, overlay18 E6F1..E700 (15 exact bytes).
; Unbound component: caller must establish supported profile/reset ownership.
BITS 16
CPU 8086
%ifdef ASPECT_EMULATE_FLAT
ORG 0xe6f1
%define aspect_dispatch_read 0x4cb4
%define aspect_emulation_selector 0x1d18
%define aspect_emulation_reset 0x20a4
%else
SEGMENT _TEXT public class=CODE use16
global aspect_emulate_command
extern aspect_dispatch_read,aspect_emulation_selector,aspect_emulation_reset
%endif
aspect_emulate_command:
 call aspect_dispatch_read
 mov [aspect_emulation_selector],ax
 mov ax,1
 push ax
 call aspect_emulation_reset
 pop bx
 ret
