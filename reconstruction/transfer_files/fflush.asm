; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_fflush
global files_at_8c55
global files_at_8c57
global files_at_8c5a
global files_at_8c5b
global files_at_8c5c
global files_at_8c5e
global files_at_8c61
global files_at_8c63
global files_at_8c65
global files_at_8c66
global files_at_8c69
global files_at_8c6b
global files_at_8c6c
global files_at_8c6f
global files_at_8c72
global files_at_8c74
global files_at_8c76
global files_at_8c78
global files_at_8c7a
global files_at_8c7d
global files_at_8c7f
global files_at_8c81
global files_at_8c85
global files_at_8c8a
global files_at_8c8c
global files_at_8c8e
global files_at_8c91
global files_at_8c94
global files_at_8c96
global files_at_8c98
global files_at_8c99
global files_at_8c9c
global files_at_8c9f
global files_at_8ca1
global files_at_8ca2
global files_at_8ca5
global files_at_8ca8
global files_at_8cab
global files_at_8cad
global files_at_8cb1
global files_at_8cb4
global files_at_8cb7
global files_at_8cb9
global files_at_8cbe
global files_at_8cc0
global files_at_8cc1
global files_at_8cc2
global files_at_8cc4
global files_at_8cc5
extern files_stream_table
extern files_extra_table
extern files_flush_all
extern files_write
%else
ORG 0x8c54
%define files_stream_table 0x7b6a
%define files_extra_table 0x7c0a
%define files_flush_all 0x8cce
%define files_write 0xa368
%endif
%include "encodings.inc"
files_fflush: push bp
files_at_8c55: mov_load bp,sp
files_at_8c57: sub sp,0x2
files_at_8c5a: push di
files_at_8c5b: push si
files_at_8c5c: sub_load di,di
files_at_8c5e: cmp [bp+0x4],di
files_at_8c61: jnz short files_at_8c6c
files_at_8c63: sub_load ax,ax
files_at_8c65: push ax
files_at_8c66: call files_flush_all
files_at_8c69: jmp short files_at_8cc0
files_at_8c6b: nop
files_at_8c6c: mov si,[bp+0x4]
files_at_8c6f: mov al,[si+0x6]
files_at_8c72: mov_load cx,ax
files_at_8c74: and al,0x3
files_at_8c76: cmp al,0x2
files_at_8c78: jnz short files_at_8cb4
files_at_8c7a: test cl,0x8
files_at_8c7d: jnz short files_at_8c8c
files_at_8c7f: mov_load bx,si
files_at_8c81: sub bx,files_stream_table
files_at_8c85: test byte [bx+files_extra_table],0x1
files_at_8c8a: jz short files_at_8cb4
files_at_8c8c: mov ax,[si]
files_at_8c8e: sub ax,[si+0x4]
files_at_8c91: mov [bp-0x2],ax
files_at_8c94: or_load ax,ax
files_at_8c96: jng short files_at_8cb4
files_at_8c98: push ax
files_at_8c99: push word [si+0x4]
files_at_8c9c: mov cl,[si+0x7]
files_at_8c9f: sub_load ch,ch
files_at_8ca1: push cx
files_at_8ca2: call files_write
files_at_8ca5: add sp,0x6
files_at_8ca8: cmp [bp-0x2],ax
files_at_8cab: jz short files_at_8cb4
files_at_8cad: or byte [si+0x6],0x20
files_at_8cb1: mov di,0xffff
files_at_8cb4: mov ax,[si+0x4]
files_at_8cb7: mov [si],ax
files_at_8cb9: mov word [si+0x2],0x0
files_at_8cbe: mov_load ax,di
files_at_8cc0: pop si
files_at_8cc1: pop di
files_at_8cc2: mov_load sp,bp
files_at_8cc4: pop bp
files_at_8cc5: ret
