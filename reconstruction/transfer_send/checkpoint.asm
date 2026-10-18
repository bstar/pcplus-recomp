; Exact original sender instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SEND_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global send_checkpoint
global send_at_904a
global send_at_904c
global send_at_904f
global send_at_9051
global send_at_9054
global send_at_9057
global send_at_905a
global send_at_905d
global send_at_9060
global send_at_9062
global send_at_9064
global send_unwind
global send_at_9067
global send_at_906a
global send_at_906c
global send_at_906e
global send_at_906f
global send_at_9072
global send_at_9075
global send_at_9078
global send_at_907b
global send_at_907d
global send_at_9080
global send_at_9083
global send_at_9085
%else
ORG 0x9048
%endif
%include "encodings.inc"
send_checkpoint: mov_load ax,bp
send_at_904a: mov_load bp,sp
send_at_904c: mov bx,[bp+0x2]
send_at_904f: mov [bx],ax
send_at_9051: mov [bx+0x2],di
send_at_9054: mov [bx+0x4],si
send_at_9057: mov [bx+0x6],sp
send_at_905a: mov cx,[bp+0x0]
send_at_905d: mov [bx+0x8],cx
send_at_9060: mov_load bp,ax
send_at_9062: xor_load ax,ax
send_at_9064: ret
send_unwind: mov_load bp,sp
send_at_9067: mov ax,[bp+0x4]
send_at_906a: or_load ax,ax
send_at_906c: jnz short send_at_906f
send_at_906e: inc ax
send_at_906f: mov bx,[bp+0x2]
send_at_9072: mov di,[bx+0x2]
send_at_9075: mov si,[bx+0x4]
send_at_9078: mov sp,[bx+0x6]
send_at_907b: mov_load bp,sp
send_at_907d: mov cx,[bx+0x8]
send_at_9080: mov [bp+0x0],cx
send_at_9083: mov bp,[bx]
send_at_9085: ret
