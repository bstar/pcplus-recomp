; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_shadow
extern window_offset8
extern window_attribute
extern window_state_7a72
extern window_state_7a74
extern window_state_7a6a
extern window_state_7a7a
%define short
%else
ORG 32050
%define window_offset8 32258
%define window_attribute 27780
%define window_state_7a72 31346
%define window_state_7a74 31348
%define window_state_7a6a 31338
%define window_state_7a7a 31354
%endif
%include "encodings.inc"
window_shadow:
L_7d32: push bp
L_7d33: mov_load bp,sp
L_7d35: push di
L_7d36: push si
L_7d37: mov bx,[bp+0x4]
L_7d3a: add bx,0x3
L_7d3d: cmp bx,[window_state_7a72]
L_7d41: jnl short L_7daa
L_7d43: dec bx
L_7d44: mov cx,[bp+0x6]
L_7d47: add cx,0x2
L_7d4a: cmp cx,[window_state_7a74]
L_7d4e: jnl short L_7daa
L_7d50: mov ax,[bp+0xa]
L_7d53: mov_load dh,al
L_7d55: inc dh
L_7d57: mov_load dl,bl
L_7d59: dec dl
L_7d5b: call window_offset8
L_7d5e: inc ax
L_7d5f: mov_load di,ax
L_7d61: sub cx,0x2
L_7d64: mov_load si,cx
L_7d66: mov ax,[bp+0xa]
L_7d69: sub_load si,ax
L_7d6b: inc si
L_7d6c: jmp short L_7d85
L_7d6e: push word [window_state_7a6a]
L_7d72: push di
L_7d73: call window_attribute
L_7d76: push word [window_state_7a6a]
L_7d7a: lea ax,[di+0x2]
L_7d7d: push ax
L_7d7e: call window_attribute
L_7d81: add di,[window_state_7a7a]
L_7d85: sub si,0x1
L_7d88: jnz short L_7d6e
L_7d8a: mov si,[bp+0x4]
L_7d8d: mov ax,[bp+0x8]
L_7d90: sub_load si,ax
L_7d92: add si,0x2
L_7d95: add di,0x2
L_7d98: jmp short L_7da5
L_7d9a: push word [window_state_7a6a]
L_7d9e: push di
L_7d9f: call window_attribute
L_7da2: sub di,0x2
L_7da5: sub si,0x1
L_7da8: jnz short L_7d9a
L_7daa: pop si
L_7dab: pop di
L_7dac: pop bp
L_7dad: ret word 0x8
