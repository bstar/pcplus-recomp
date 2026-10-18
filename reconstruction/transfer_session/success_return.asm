; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_success_return
global session_at_daa1
global session_at_daa2
global session_at_daa3
global session_at_daa5
global session_at_daa6
%else
ORG 0xda9e
%endif
%include "encodings.inc"
session_success_return: mov ax,0x1
session_at_daa1: pop si
session_at_daa2: pop di
session_at_daa3: mov_load sp,bp
session_at_daa5: pop bp
session_at_daa6: ret
