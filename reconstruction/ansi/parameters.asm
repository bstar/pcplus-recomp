; Recovered PCPlus 2.01 ANSI parameter reader, overlay 12.
; REA Evidence ev_eee26e941827e00c190eae7fd9e329a0be13e93287e5be2fd0722da4241d6207.
; Original layout only. The original lacks digit/parameter bounds; do not expose it to untrusted input.
BITS 16
CPU 8086
ORG 0xe3f2
%include "encodings.inc"
ansi_read_parameter:
L_e3f2: push bp
L_e3f3: mov_load bp,sp
L_e3f5: sub sp,0x20
L_e3f8: push di
L_e3f9: push si
L_e3fa: sub_load di,di
L_e3fc: jmp short L_e407
L_e3fe: cmp si,0x3a
L_e401: jnl L_e411
L_e403: mov [bp+di-0x20],al
L_e406: inc di
L_e407: call 0x5ca0
L_e40a: mov_load si,ax
L_e40c: cmp si,0x2f
L_e40f: jg L_e3fe
L_e411: cmp si,0x3b
L_e414: jnz L_e41a
L_e416: or_load di,di
L_e418: jz L_e446
L_e41a: or_load si,si
L_e41c: jz L_e407
L_e41e: cmp si,0x7f
L_e421: jz L_e407
L_e423: cmp si,0x1b
L_e426: jz L_e43a
L_e428: or_load si,si
L_e42a: jl L_e44b
L_e42c: cmp si,0x1b
L_e42f: jnl L_e44b
L_e431: push si
L_e432: call 0x610
L_e435: add sp,0x2
L_e438: jmp short L_e407
L_e43a: call 0xabde
L_e43d: mov ax,0x41
L_e440: pop si
L_e441: pop di
L_e442: mov_load sp,bp
L_e444: pop bp
L_e445: ret
L_e446: mov byte [bp+di-0x20],0x30
L_e44a: inc di
L_e44b: or_load di,di
L_e44d: jz L_e46e
L_e44f: mov byte [bp+di-0x20],0x0
L_e453: lea ax,[bp-0x20]
L_e456: push ax
L_e457: call 0x984e
L_e45a: add sp,0x2
L_e45d: mov bx,[0xcb5c]
L_e461: shl bx,1
L_e463: mov [bx-0x34c4],ax
L_e467: inc word [0xcb5c]
L_e46b: jmp short L_e494
L_e46d: nop
L_e46e: cmp si,0x3f
L_e471: jnz L_e486
L_e473: mov word [0xceac],0x1
L_e479: mov [0xcd38],si
L_e47d: mov ax,0x44
L_e480: pop si
L_e481: pop di
L_e482: mov_load sp,bp
L_e484: pop bp
L_e485: ret
L_e486: cmp si,0x3e
L_e489: jnz L_e494
L_e48b: mov word [0xcee2],0x1
L_e491: jmp short L_e479
L_e493: nop
L_e494: mov [0xcd38],si
L_e498: mov ax,0x53
L_e49b: pop si
L_e49c: pop di
L_e49d: mov_load sp,bp
L_e49f: pop bp
L_e4a0: ret
