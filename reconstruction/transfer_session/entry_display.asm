; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_at_d73c
global session_at_d73f
global session_at_d740
global session_at_d744
global session_at_d747
global session_at_d748
global session_at_d74b
global session_at_d74e
global session_at_d74f
extern session_display_path
extern session_ui_attribute
extern session_ui_print
extern session_handshake_enter
%else
ORG 0xd73c
%define session_display_path 0x3ea4
%define session_ui_attribute 0x1f76
%define session_ui_print 0x6bf0
%endif
%include "encodings.inc"
session_at_d73c: mov ax,0x73e
session_at_d73f: push ax
session_at_d740: push word [session_ui_attribute]
session_at_d744: lea ax,[bp-0x56]
session_at_d747: push ax
session_at_d748: call session_display_path
session_at_d74b: add sp,0x2
session_at_d74e: push ax
session_at_d74f: call session_ui_print
%ifdef TRANSFER_SESSION_OMF
jmp session_handshake_enter
%endif
