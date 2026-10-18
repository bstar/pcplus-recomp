; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_longjmp
global session_at_9067
global session_at_906a
global session_at_906c
global session_at_906e
global session_at_906f
global session_at_9072
global session_at_9075
global session_at_9078
global session_at_907b
global session_at_907d
global session_at_9080
global session_at_9083
global session_at_9085
%else
ORG 0x9065
%endif
%include "encodings.inc"
session_longjmp: mov_load bp,sp
session_at_9067: mov ax,[bp+0x4]
session_at_906a: or_load ax,ax
session_at_906c: jnz short session_at_906f
session_at_906e: inc ax
session_at_906f: mov bx,[bp+0x2]
session_at_9072: mov di,[bx+0x2]
session_at_9075: mov si,[bx+0x4]
session_at_9078: mov sp,[bx+0x6]
session_at_907b: mov_load bp,sp
session_at_907d: mov cx,[bx+0x8]
session_at_9080: mov [bp+0x0],cx
session_at_9083: mov bp,[bx]
session_at_9085: ret
