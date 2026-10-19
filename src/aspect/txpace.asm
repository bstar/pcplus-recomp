; Exact native6B72..6B97 with maintained nearcdecl/clock/IF adapters.
; Evidenceev_a30bfa2cee5690318dc8252472fd4570367e365219605a4b4a1e2253170377fc.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_TXPACE_FLAT
ORG 0x6b72
%define aspect_txpace_floor 0x7a4e
%define _aspect_txpace_count 0x7ac4
%else
SEGMENT _TEXT public class=CODE use16
extern _aspect_txpace_count
global aspect_txpace_native_delay
%endif
aspect_txpace_native_delay:
L_6b72: mov_load bx,sp
L_6b74: mov dx, word [bx + 0x2]
L_6b77: cmp dx, 0x0
L_6b7a: jz L_6b95
L_6b7c: mov ax, ds
L_6b7e: mov es, ax
L_6b80: mov bx, aspect_txpace_floor
L_6b83: mov cx, word [_aspect_txpace_count]
L_6b87: sub cx, 0x1
L_6b8a: adc ax, strict word 0x0
L_6b8d: cmp cx, word es:[bx]
L_6b90: jnz L_6b87
L_6b92: dec dx
L_6b93: jnz L_6b83
L_6b95: ret 0x2

%ifndef ASPECT_TXPACE_FLAT
global _aspect_txpace_native_one,_aspect_txpace_ticks
GLOBAL _aspect_txpace_flags,_aspect_txpace_restore_if
_aspect_txpace_native_one:
 push bx
 push es
 mov ax,1
 push ax
 call aspect_txpace_native_delay
 pop es
 pop bx
 ret
_aspect_txpace_ticks:
 pushf
 cli
 push es
 xor ax,ax
 mov es,ax
 mov ax,[es:0x46c]
 mov dx,[es:0x46e]
 pop es
 popf
 ret
_aspect_txpace_flags:
 pushf
 pop ax
 ret
_aspect_txpace_restore_if:
 push bp
 mov bp,sp
 pushf
 pop ax
 and ax,0xfdff
 mov dx,[bp+4]
 and dx,0x200
 or ax,dx
 push ax
 popf
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
aspect_txpace_floor: dw 0
%endif
