; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_failure_cleanup_argument
global session_failure_return
global session_at_d736
global session_at_d737
global session_at_d738
global session_at_d73a
global session_at_d73b
%else
ORG 0xd731
%endif
%include "encodings.inc"
session_failure_cleanup_argument: add sp,0x2
session_failure_return: sub_load ax,ax
session_at_d736: pop si
session_at_d737: pop di
session_at_d738: mov_load sp,bp
session_at_d73a: pop bp
session_at_d73b: ret
