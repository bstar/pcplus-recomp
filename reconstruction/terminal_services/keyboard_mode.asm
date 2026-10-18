; Recovered PCPlus 2.01 terminal support instructions; see docs/TERMINAL_SERVICES.md.
BITS 16
CPU 8086
%ifdef TERMINAL_SERVICES_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_keyboard_mode
extern terminal_dec_keys
extern terminal_keymap
extern terminal_keymap_end
%define short
%else
ORG 0xb4e
%define terminal_dec_keys 0x8fe8
%define terminal_keymap 0x3378
%define terminal_keymap_end 0x372c
%endif
%include "encodings.inc"
terminal_keyboard_mode:
L_0b4e: push bp
L_0b4f: mov_load bp,sp
L_0b51: sub sp,0x8
L_0b54: push di
L_0b55: push si
L_0b56: mov byte [bp-0x8],0x1b
L_0b5a: mov byte [bp-0x7],0x5b
L_0b5e: cmp word [bp+0x4],0x5b
L_0b62: jnz short L_0b68
L_0b64: mov byte [bp-0x7],0x4f
L_0b68: mov byte [bp-0x5],0x0
L_0b6c: cmp word [terminal_dec_keys],0x0
L_0b71: jz short L_0bba
L_0b73: mov word [bp-0x4],0x41
L_0b78: mov al,[bp-0x4]
L_0b7b: mov [bp-0x6],al
L_0b7e: mov dx,terminal_keymap
L_0b81: lea di,[bp-0x8]
L_0b84: mov_load si,dx
L_0b86: push ss
L_0b87: pop es
L_0b88: mov cx,0xffff
L_0b8b: xor_load ax,ax
L_0b8d: repne scasb
L_0b8f: not cx
L_0b91: sub_load di,cx
L_0b93: repe cmpsb
L_0b95: jz short L_0b9c
L_0b97: sbb_load ax,ax
L_0b99: sbb ax,strict word 0xffff
L_0b9c: or_load ax,ax
L_0b9e: jnz short L_0ba8
L_0ba0: mov al,[bp+0x4]
L_0ba3: mov_load bx,dx
L_0ba5: mov [bx+0x1],al
L_0ba8: add dx,0xc
L_0bab: cmp dx,terminal_keymap_end
L_0baf: jc short L_0b81
L_0bb1: inc word [bp-0x4]
L_0bb4: cmp word [bp-0x4],0x45
L_0bb8: jl short L_0b78
L_0bba: pop si
L_0bbb: pop di
L_0bbc: mov_load sp,bp
L_0bbe: pop bp
L_0bbf: ret
