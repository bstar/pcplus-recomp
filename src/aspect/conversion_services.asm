; Exact PCPlus2.01 integer ASCII CRT services; no host libc substitution.
; OriginalSHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Near caller-clean ABI, DS=SS, DF=0. BP/SI/DI preserved, ES/flags/BX/CX volatile.
; atoi/atol(str) share32bit DX:AX accumulator; atoi callers consume low AX.
; Whitespace ONLY SP/TAB; optional sign; decimal prefix; wraps32bits/noerrno.
; itoa(word,dest,radix),ltoa(low,high,dest,radix) return destAX.
; format_long/format_tail are INTERIOR shared tails, not callable functions:
; their BP frame/savedSI/DI/BLsigned flag are supplied by itoa/ltoa prefixes.
; DX is the parse high-result and otherwise volatile.
; Signed only radix10; nondecimal word is unsigned16,long unsigned32.
; Native formatter has NO radix or destination bound checks; live callers must
; supply radix2..36 and sufficient destination. Bad radix0 can divide-fault;
; radix1/nonzero may not terminate. Such undefined cases are not made safe here.
; strcspn(str,reject) constructs an exact256bit stack set; no ctype dependency.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CONVERSION_SERVICES_FLAT
%if ASPECT_CONVERSION_SERVICES_UNIT=1
ORG 0x984e
%elif ASPECT_CONVERSION_SERVICES_UNIT=2
ORG 0x9b32
%elif ASPECT_CONVERSION_SERVICES_UNIT=3
ORG 0x8e6c
%elif ASPECT_CONVERSION_SERVICES_UNIT=4
ORG 0x9ae8
%elif ASPECT_CONVERSION_SERVICES_UNIT=5
ORG 0xa5e8
%elif ASPECT_CONVERSION_SERVICES_UNIT=6
ORG 0xa7ce
%elif ASPECT_CONVERSION_SERVICES_UNIT=7
ORG 0x9b36
%else
%error Select ASPECT_CONVERSION_SERVICES_UNIT1..7
%endif
%define aspect_conversion_atoi 0x984e
%define aspect_conversion_atol 0x9b32
%define aspect_conversion_itoa 0x8e6c
%define aspect_conversion_ltoa 0x9ae8
%define aspect_conversion_format_long 0xa5e8
%define aspect_conversion_parse 0xa7ce
%define aspect_conversion_strcspn 0x9b36
%define aspect_conversion_format_tail 0xa5f4
%else
%define ASPECT_CONVERSION_SERVICES_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_conversion_atoi
global aspect_conversion_atol
global aspect_conversion_itoa
global aspect_conversion_ltoa
global aspect_conversion_format_long
global aspect_conversion_parse
global aspect_conversion_strcspn
global aspect_conversion_format_tail
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=1
; REA ev_e7e8e15e2b1bfccd55a8d31ec50252a97fe905ed5dbea04e319911fb57affda2; resident984e..9851.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_atoi:
%endif
L_984e: jmp aspect_conversion_parse
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=2
; REA ev_a9da5bc7487d9c4e7dc8ea5ce54d32c81b563699f94048d074f3930778d35d7a; resident9b32..9b35.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_atol:
%endif
L_9b32: jmp aspect_conversion_parse
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=3
; REA ev_bba5e16b310a48caf85e1d0c82063833b72b49ca21c2d1ce8f8991bbc8b66786; resident8e6c..8e87.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_itoa:
%endif
L_8e6c: push bp
L_8e6d: mov_load bp, sp
L_8e6f: push si
L_8e70: push di
L_8e71: mov bl, 0x1
L_8e73: mov cx, word [bp + 0x8]
L_8e76: mov ax, word [bp + 0x4]
L_8e79: xor_load dx, dx
L_8e7b: cmp cx, 0xa
L_8e7e: jnz L_8e81
L_8e80: cwd
L_8e81: mov di, word [bp + 0x6]
L_8e84: jmp aspect_conversion_format_tail
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=4
; REA ev_145a03beca170ef491b586e32678562f71403a7041bb66da81714350e77f23d4; resident9ae8..9af2.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_ltoa:
%endif
L_9ae8: push bp
L_9ae9: mov_load bp, sp
L_9aeb: push si
L_9aec: push di
L_9aed: mov bl, 0x1
L_9aef: jmp aspect_conversion_format_long
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=5
; REA ev_ad75518be49334c870eefd10ff797ce2e50ac1769fa9646088efc645cb336911; residenta5e8..a647.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_format_long:
%endif
L_a5e8: mov cx, word [bp + 0xa]
L_a5eb: mov ax, word [bp + 0x4]
L_a5ee: mov dx, word [bp + 0x6]
L_a5f1: mov di, word [bp + 0x8]
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_format_tail:
%endif
L_a5f4: push di
L_a5f5: push ds
L_a5f6: pop es
L_a5f7: cld
L_a5f8: xchg ax, bx
L_a5f9: or_load al, al
L_a5fb: jz L_a610
L_a5fd: cmp cx, 0xa
L_a600: jnz L_a610
L_a602: or_load dx, dx
L_a604: jns L_a610
L_a606: mov al, 0x2d
L_a608: stosb
L_a609: neg bx
L_a60b: adc dx, 0x0
L_a60e: neg dx
L_a610: mov_load si, di
L_a612: xchg ax, dx
L_a613: xor_load dx, dx
L_a615: or_load ax, ax
L_a617: jz L_a61b
L_a619: div cx
L_a61b: xchg ax, bx
L_a61c: div cx
L_a61e: xchg ax, dx
L_a61f: xchg dx, bx
L_a621: add al, 0x30
L_a623: cmp al, 0x39
L_a625: jbe L_a629
L_a627: add al, 0x27
L_a629: stosb
L_a62a: mov_load ax, dx
L_a62c: or_load ax, bx
L_a62e: jnz L_a612
L_a630: mov byte [di], al
L_a632: dec di
L_a633: lodsb
L_a634: xchg byte [di], al
L_a636: mov byte [si + -0x1], al
L_a639: lea ax, [si + 0x1]
L_a63c: cmp_load ax, di
L_a63e: jc L_a632
L_a640: pop ax
L_a641: pop di
L_a642: pop si
L_a643: mov_load sp, bp
L_a645: pop bp
L_a646: ret
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=6
; REA ev_dd1ca86c9b854a668eac28d03131080234019b98df4bdb707e59254ed596d9e1; residenta7ce..a822.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_parse:
%endif
L_a7ce: push bp
L_a7cf: mov_load bp, sp
L_a7d1: push di
L_a7d2: push si
L_a7d3: mov si, word [bp + 0x4]
L_a7d6: xor_load ax, ax
L_a7d8: cwd
L_a7d9: xor_load bx, bx
L_a7db: lodsb
L_a7dc: cmp al, 0x20
L_a7de: jz L_a7db
L_a7e0: cmp al, 0x9
L_a7e2: jz L_a7db
L_a7e4: push ax
L_a7e5: cmp al, 0x2d
L_a7e7: jz L_a7ed
L_a7e9: cmp al, 0x2b
L_a7eb: jnz L_a7ee
L_a7ed: lodsb
L_a7ee: cmp al, 0x39
L_a7f0: ja L_a811
L_a7f2: sub al, 0x30
L_a7f4: jc L_a811
L_a7f6: shl bx, 0x1
L_a7f8: rcl dx, 0x1
L_a7fa: mov_load cx, bx
L_a7fc: mov_load di, dx
L_a7fe: shl bx, 0x1
L_a800: rcl dx, 0x1
L_a802: shl bx, 0x1
L_a804: rcl dx, 0x1
L_a806: add_load bx, cx
L_a808: adc_load dx, di
L_a80a: add_load bx, ax
L_a80c: adc dx, 0x0
L_a80f: jmp L_a7ed
L_a811: pop ax
L_a812: cmp al, 0x2d
L_a814: xchg ax, bx
L_a815: jnz L_a81e
L_a817: neg ax
L_a819: adc dx, 0x0
L_a81c: neg dx
L_a81e: pop si
L_a81f: pop di
L_a820: pop bp
L_a821: ret
%endif
%if ASPECT_CONVERSION_SERVICES_UNIT=0 || ASPECT_CONVERSION_SERVICES_UNIT=7
; REA ev_65bd9310fff453ae563a96be181584c6ed2684511e9fcddb91729bb0c72658bf; resident9b36..9b90.
%ifndef ASPECT_CONVERSION_SERVICES_FLAT
aspect_conversion_strcspn:
%endif
L_9b36: push bp
L_9b37: mov_load bp, sp
L_9b39: sub sp, 0x20
L_9b3c: push si
L_9b3d: push di
L_9b3e: mov si, word [bp + 0x6]
L_9b41: mov ax, ss
L_9b43: mov es, ax
L_9b45: mov cx, 0x10
L_9b48: xor_load ax, ax
L_9b4a: lea di, [bp + -0x20]
L_9b4d: rep stosw
L_9b4f: lodsb
L_9b50: or_load al, al
L_9b52: jz L_9b68
L_9b54: mov_load di, ax
L_9b56: mov_load cx, ax
L_9b58: mov al, 0x1
L_9b5a: and cl, 0x7
L_9b5d: shl al, cl
L_9b5f: mov cl, 0x3
L_9b61: shr di, cl
L_9b63: or byte [bp + di + -0x20], al
L_9b66: jmp L_9b4f
L_9b68: mov si, word [bp + 0x4]
L_9b6b: mov bx, 0xffff
L_9b6e: inc bx
L_9b6f: lodsb
L_9b70: and ax, 0xff
L_9b73: jz L_9b89
L_9b75: mov_load di, ax
L_9b77: mov_load cx, ax
L_9b79: mov al, 0x1
L_9b7b: and cl, 0x7
L_9b7e: shl al, cl
L_9b80: mov cl, 0x3
L_9b82: shr di, cl
L_9b84: and al, byte [bp + di + -0x20]
L_9b87: jz L_9b6e
L_9b89: xchg ax, bx
L_9b8a: pop di
L_9b8b: pop si
L_9b8c: mov_load sp, bp
L_9b8e: pop bp
L_9b8f: ret
%endif
