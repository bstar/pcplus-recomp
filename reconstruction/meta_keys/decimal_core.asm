; Recovered PCPlus 2.01 KEY action instructions; see docs/META_KEYS.md.
BITS 16
CPU 8086
%ifdef META_KEYS_OMF
SEGMENT _TEXT public class=CODE use16
global meta_keys_decimal_core,meta_keys_decimal_body
%define short
%else
ORG 0xa5e8
%endif
%include "encodings.inc"
meta_keys_decimal_core:
L_a5e8: mov cx,[bp+0xa]
L_a5eb: mov ax,[bp+0x4]
L_a5ee: mov dx,[bp+0x6]
L_a5f1: mov di,[bp+0x8]
meta_keys_decimal_body:
L_a5f4: push di
L_a5f5: push ds
L_a5f6: pop es
L_a5f7: cld
L_a5f8: xchg ax,bx
L_a5f9: or_load al,al
L_a5fb: jz short L_a610
L_a5fd: cmp cx,0xa
L_a600: jnz short L_a610
L_a602: or_load dx,dx
L_a604: jns short L_a610
L_a606: mov al,0x2d
L_a608: stosb
L_a609: neg bx
L_a60b: adc dx,0x0
L_a60e: neg dx
L_a610: mov_load si,di
L_a612: xchg ax,dx
L_a613: xor_load dx,dx
L_a615: or_load ax,ax
L_a617: jz short L_a61b
L_a619: div cx
L_a61b: xchg ax,bx
L_a61c: div cx
L_a61e: xchg ax,dx
L_a61f: xchg dx,bx
L_a621: add al,0x30
L_a623: cmp al,0x39
L_a625: jna short L_a629
L_a627: add al,0x27
L_a629: stosb
L_a62a: mov_load ax,dx
L_a62c: or_load ax,bx
L_a62e: jnz short L_a612
L_a630: mov [di],al
L_a632: dec di
L_a633: lodsb
L_a634: xchg al,[di]
L_a636: mov [si-0x1],al
L_a639: lea ax,[si+0x1]
L_a63c: cmp_load ax,di
L_a63e: jc short L_a632
L_a640: pop ax
L_a641: pop di
L_a642: pop si
L_a643: mov_load sp,bp
L_a645: pop bp
L_a646: ret
