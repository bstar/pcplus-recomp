; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_decimal16
extern meta_keys_decimal_body
%define short
%else
ORG 0x8e6c
%define meta_keys_decimal_body 0xa5f4
%endif
%include "encodings.inc"
meta_keys_decimal16:
L_8e6c: push bp
L_8e6d: mov_load bp,sp
L_8e6f: push si
L_8e70: push di
L_8e71: mov bl,0x1
L_8e73: mov cx,[bp+0x8]
L_8e76: mov ax,[bp+0x4]
L_8e79: xor_load dx,dx
L_8e7b: cmp cx,0xa
L_8e7e: jnz short L_8e81
L_8e80: cwd
L_8e81: mov di,[bp+0x6]
L_8e84: jmp near meta_keys_decimal_body
