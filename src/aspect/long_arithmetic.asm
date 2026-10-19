; PCPlus2.01 resident signed long arithmetic, recovered from REA assembly.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Near DS=SS, DF=0. Value entries take two DWORD stack operands, RET8,
; return DX:AX. In-place entries take near pointer plus DWORD (RET6) or
; word shift count (RET4). BP/BX/SI/DI preserved; AX/CX/DX/flags volatile.
; Shift helpers use count low byte without286+ count masking. Arithmetic wraps.
; Native direct divide-by-zero raises INT0; callers must enforce their policy.
; Signed minimum/-1 long quotient wraps to80000000; no float approximation.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_LONG_FLAT
%if ASPECT_LONG_UNIT=1
ORG 0x9950
%elif ASPECT_LONG_UNIT=2
ORG 0x9a1a
%elif ASPECT_LONG_UNIT=3
ORG 0x9ab4
%elif ASPECT_LONG_UNIT=4
ORG 0x9af2
%elif ASPECT_LONG_UNIT=5
ORG 0x9b12
%elif ASPECT_LONG_UNIT=6
ORG 0x9b90
%elif ASPECT_LONG_UNIT=7
ORG 0x9bb0
%elif ASPECT_LONG_UNIT=8
ORG 0x9bcc
%elif ASPECT_LONG_UNIT=9
ORG 0x9c7c
%elif ASPECT_LONG_UNIT=10
ORG 0x9d1c
%else
%error Select ASPECT_LONG_UNIT1..10
%endif
%define native_long_multiply_value 0x9950
%define native_long_divide_value 0x9a1a
%define native_long_shift_left_value 0x9ab4
%define native_long_divide 0x9af2
%define native_long_modulo 0x9b12
%define native_long_multiply 0x9b90
%define native_long_shift_left 0x9bb0
%define native_long_shift_right 0x9bcc
%define native_long_modulo_value 0x9c7c
%define native_long_shift_right_value 0x9d1c
%else
%define ASPECT_LONG_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_long_multiply_value
%define native_long_multiply_value aspect_long_multiply_value
global aspect_long_divide_value
%define native_long_divide_value aspect_long_divide_value
global aspect_long_shift_left_value
%define native_long_shift_left_value aspect_long_shift_left_value
global aspect_long_divide
%define native_long_divide aspect_long_divide
global aspect_long_modulo
%define native_long_modulo aspect_long_modulo
global aspect_long_multiply
%define native_long_multiply aspect_long_multiply
global aspect_long_shift_left
%define native_long_shift_left aspect_long_shift_left
global aspect_long_shift_right
%define native_long_shift_right aspect_long_shift_right
global aspect_long_modulo_value
%define native_long_modulo_value aspect_long_modulo_value
global aspect_long_shift_right_value
%define native_long_shift_right_value aspect_long_shift_right_value
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=1
aspect_long_multiply_value:
.L9950:
 push bp
.L9951:
 mov_load bp, sp
.L9953:
 mov ax, word [bp + 0x6]
.L9956:
 mov cx, word [bp + 0xa]
.L9959:
 or_load cx, ax
.L995b:
 mov cx, word [bp + 0x8]
.L995e:
 jnz .L9969
.L9960:
 mov ax, word [bp + 0x4]
.L9963:
 mul cx
.L9965:
 pop bp
.L9966:
 ret 0x8
.L9969:
 push bx
.L996a:
 mul cx
.L996c:
 mov_load bx, ax
.L996e:
 mov ax, word [bp + 0x4]
.L9971:
 mul word [bp + 0xa]
.L9974:
 add_load bx, ax
.L9976:
 mov ax, word [bp + 0x4]
.L9979:
 mul cx
.L997b:
 add_load dx, bx
.L997d:
 pop bx
.L997e:
 pop bp
.L997f:
 ret 0x8
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=2
aspect_long_divide_value:
.L9a1a:
 push bp
.L9a1b:
 mov_load bp, sp
.L9a1d:
 push di
.L9a1e:
 push si
.L9a1f:
 push bx
.L9a20:
 xor_load di, di
.L9a22:
 mov ax, word [bp + 0x6]
.L9a25:
 or_load ax, ax
.L9a27:
 jge .L9a3a
.L9a29:
 inc di
.L9a2a:
 mov dx, word [bp + 0x4]
.L9a2d:
 neg ax
.L9a2f:
 neg dx
.L9a31:
 sbb ax, strict word 0x0
.L9a34:
 mov word [bp + 0x6], ax
.L9a37:
 mov word [bp + 0x4], dx
.L9a3a:
 mov ax, word [bp + 0xa]
.L9a3d:
 or_load ax, ax
.L9a3f:
 jge .L9a52
.L9a41:
 inc di
.L9a42:
 mov dx, word [bp + 0x8]
.L9a45:
 neg ax
.L9a47:
 neg dx
.L9a49:
 sbb ax, strict word 0x0
.L9a4c:
 mov word [bp + 0xa], ax
.L9a4f:
 mov word [bp + 0x8], dx
.L9a52:
 or_load ax, ax
.L9a54:
 jnz .L9a6b
.L9a56:
 mov cx, word [bp + 0x8]
.L9a59:
 mov ax, word [bp + 0x6]
.L9a5c:
 xor_load dx, dx
.L9a5e:
 div cx
.L9a60:
 mov_load bx, ax
.L9a62:
 mov ax, word [bp + 0x4]
.L9a65:
 div cx
.L9a67:
 mov_load dx, bx
.L9a69:
 jmp .L9aa3
.L9a6b:
 mov_load bx, ax
.L9a6d:
 mov cx, word [bp + 0x8]
.L9a70:
 mov dx, word [bp + 0x6]
.L9a73:
 mov ax, word [bp + 0x4]
.L9a76:
 shr bx, 0x1
.L9a78:
 rcr cx, 0x1
.L9a7a:
 shr dx, 0x1
.L9a7c:
 rcr ax, 0x1
.L9a7e:
 or_load bx, bx
.L9a80:
 jnz .L9a76
.L9a82:
 div cx
.L9a84:
 mov_load si, ax
.L9a86:
 mul word [bp + 0xa]
.L9a89:
 xchg ax, cx
.L9a8a:
 mov ax, word [bp + 0x8]
.L9a8d:
 mul si
.L9a8f:
 add_load dx, cx
.L9a91:
 jc .L9a9f
.L9a93:
 cmp dx, word [bp + 0x6]
.L9a96:
 ja .L9a9f
.L9a98:
 jc .L9aa0
.L9a9a:
 cmp ax, word [bp + 0x4]
.L9a9d:
 jbe .L9aa0
.L9a9f:
 dec si
.L9aa0:
 xor_load dx, dx
.L9aa2:
 xchg ax, si
.L9aa3:
 dec di
.L9aa4:
 jnz .L9aad
.L9aa6:
 neg dx
.L9aa8:
 neg ax
.L9aaa:
 sbb dx, 0x0
.L9aad:
 pop bx
.L9aae:
 pop si
.L9aaf:
 pop di
.L9ab0:
 pop bp
.L9ab1:
 ret 0x8
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=3
aspect_long_shift_left_value:
.L9ab4:
 xor_load ch, ch
.L9ab6:
 jcxz .L9abe
.L9ab8:
 shl ax, 0x1
.L9aba:
 rcl dx, 0x1
.L9abc:
 loop .L9ab8
.L9abe:
 ret
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=4
aspect_long_divide:
.L9af2:
 push bp
.L9af3:
 mov_load bp, sp
.L9af5:
 push bx
.L9af6:
 mov bx, word [bp + 0x4]
.L9af9:
 push word [bp + 0x8]
.L9afc:
 push word [bp + 0x6]
.L9aff:
 push word [bx + 0x2]
.L9b02:
 push word [bx]
.L9b04:
 call native_long_divide_value
.L9b07:
 mov word [bx + 0x2], dx
.L9b0a:
 mov word [bx], ax
.L9b0c:
 pop bx
.L9b0d:
 pop bp
.L9b0e:
 ret 0x6
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=5
aspect_long_modulo:
.L9b12:
 push bp
.L9b13:
 mov_load bp, sp
.L9b15:
 push bx
.L9b16:
 mov bx, word [bp + 0x4]
.L9b19:
 push word [bp + 0x8]
.L9b1c:
 push word [bp + 0x6]
.L9b1f:
 push word [bx + 0x2]
.L9b22:
 push word [bx]
.L9b24:
 call native_long_modulo_value
.L9b27:
 mov word [bx + 0x2], dx
.L9b2a:
 mov word [bx], ax
.L9b2c:
 pop bx
.L9b2d:
 pop bp
.L9b2e:
 ret 0x6
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=6
aspect_long_multiply:
.L9b90:
 push bp
.L9b91:
 mov_load bp, sp
.L9b93:
 push bx
.L9b94:
 mov bx, word [bp + 0x4]
.L9b97:
 push word [bp + 0x8]
.L9b9a:
 push word [bp + 0x6]
.L9b9d:
 push word [bx + 0x2]
.L9ba0:
 push word [bx]
.L9ba2:
 call native_long_multiply_value
.L9ba5:
 mov word [bx], ax
.L9ba7:
 mov word [bx + 0x2], dx
.L9baa:
 pop bx
.L9bab:
 pop bp
.L9bac:
 ret 0x6
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=7
aspect_long_shift_left:
.L9bb0:
 push bp
.L9bb1:
 mov_load bp, sp
.L9bb3:
 push bx
.L9bb4:
 mov bx, word [bp + 0x4]
.L9bb7:
 mov ax, word [bx]
.L9bb9:
 mov dx, word [bx + 0x2]
.L9bbc:
 mov cx, word [bp + 0x6]
.L9bbf:
 call native_long_shift_left_value
.L9bc2:
 mov word [bx], ax
.L9bc4:
 mov word [bx + 0x2], dx
.L9bc7:
 pop bx
.L9bc8:
 pop bp
.L9bc9:
 ret 0x4
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=8
aspect_long_shift_right:
.L9bcc:
 push bp
.L9bcd:
 mov_load bp, sp
.L9bcf:
 push bx
.L9bd0:
 mov bx, word [bp + 0x4]
.L9bd3:
 mov ax, word [bx]
.L9bd5:
 mov dx, word [bx + 0x2]
.L9bd8:
 mov cx, word [bp + 0x6]
.L9bdb:
 call native_long_shift_right_value
.L9bde:
 mov word [bx], ax
.L9be0:
 mov word [bx + 0x2], dx
.L9be3:
 pop bx
.L9be4:
 pop bp
.L9be5:
 ret 0x4
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=9
aspect_long_modulo_value:
.L9c7c:
 push bp
.L9c7d:
 mov_load bp, sp
.L9c7f:
 push bx
.L9c80:
 push di
.L9c81:
 xor_load di, di
.L9c83:
 mov ax, word [bp + 0x6]
.L9c86:
 or_load ax, ax
.L9c88:
 jge .L9c9b
.L9c8a:
 inc di
.L9c8b:
 mov dx, word [bp + 0x4]
.L9c8e:
 neg ax
.L9c90:
 neg dx
.L9c92:
 sbb ax, strict word 0x0
.L9c95:
 mov word [bp + 0x6], ax
.L9c98:
 mov word [bp + 0x4], dx
.L9c9b:
 mov ax, word [bp + 0xa]
.L9c9e:
 or_load ax, ax
.L9ca0:
 jge .L9cb2
.L9ca2:
 mov dx, word [bp + 0x8]
.L9ca5:
 neg ax
.L9ca7:
 neg dx
.L9ca9:
 sbb ax, strict word 0x0
.L9cac:
 mov word [bp + 0xa], ax
.L9caf:
 mov word [bp + 0x8], dx
.L9cb2:
 or_load ax, ax
.L9cb4:
 jnz .L9cce
.L9cb6:
 mov cx, word [bp + 0x8]
.L9cb9:
 mov ax, word [bp + 0x6]
.L9cbc:
 xor_load dx, dx
.L9cbe:
 div cx
.L9cc0:
 mov ax, word [bp + 0x4]
.L9cc3:
 div cx
.L9cc5:
 mov_load ax, dx
.L9cc7:
 xor_load dx, dx
.L9cc9:
 dec di
.L9cca:
 jns .L9d0f
.L9ccc:
 jmp .L9d16
.L9cce:
 mov_load bx, ax
.L9cd0:
 mov cx, word [bp + 0x8]
.L9cd3:
 mov dx, word [bp + 0x6]
.L9cd6:
 mov ax, word [bp + 0x4]
.L9cd9:
 shr bx, 0x1
.L9cdb:
 rcr cx, 0x1
.L9cdd:
 shr dx, 0x1
.L9cdf:
 rcr ax, 0x1
.L9ce1:
 or_load bx, bx
.L9ce3:
 jnz .L9cd9
.L9ce5:
 div cx
.L9ce7:
 mov_load cx, ax
.L9ce9:
 mul word [bp + 0xa]
.L9cec:
 xchg ax, cx
.L9ced:
 mul word [bp + 0x8]
.L9cf0:
 add_load dx, cx
.L9cf2:
 jc .L9d00
.L9cf4:
 cmp dx, word [bp + 0x6]
.L9cf7:
 ja .L9d00
.L9cf9:
 jc .L9d06
.L9cfb:
 cmp ax, word [bp + 0x4]
.L9cfe:
 jbe .L9d06
.L9d00:
 sub ax, word [bp + 0x8]
.L9d03:
 sbb dx, word [bp + 0xa]
.L9d06:
 sub ax, word [bp + 0x4]
.L9d09:
 sbb dx, word [bp + 0x6]
.L9d0c:
 dec di
.L9d0d:
 jns .L9d16
.L9d0f:
 neg dx
.L9d11:
 neg ax
.L9d13:
 sbb dx, 0x0
.L9d16:
 pop di
.L9d17:
 pop bx
.L9d18:
 pop bp
.L9d19:
 ret 0x8
%endif
%if ASPECT_LONG_UNIT=0 || ASPECT_LONG_UNIT=10
aspect_long_shift_right_value:
.L9d1c:
 xor_load ch, ch
.L9d1e:
 jcxz .L9d26
.L9d20:
 sar dx, 0x1
.L9d22:
 rcr ax, 0x1
.L9d24:
 loop .L9d20
.L9d26:
 ret
%endif
