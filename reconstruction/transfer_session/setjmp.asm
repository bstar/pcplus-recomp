; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_setjmp
global session_at_904a
global session_at_904c
global session_at_904f
global session_at_9051
global session_at_9054
global session_at_9057
global session_at_905a
global session_at_905d
global session_at_9060
global session_at_9062
global session_at_9064
%else
ORG 0x9048
%endif
%include "encodings.inc"
session_setjmp: mov_load ax,bp
session_at_904a: mov_load bp,sp
session_at_904c: mov bx,[bp+0x2]
session_at_904f: mov [bx],ax
session_at_9051: mov [bx+0x2],di
session_at_9054: mov [bx+0x4],si
session_at_9057: mov [bx+0x6],sp
session_at_905a: mov cx,[bp+0x0]
session_at_905d: mov [bx+0x8],cx
session_at_9060: mov_load bp,ax
session_at_9062: xor_load ax,ax
session_at_9064: ret
