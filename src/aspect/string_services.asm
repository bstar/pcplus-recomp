; PCPlus2.01 exact string CRT helpers, bounded byte/index wrappers,
; integer destination store and comparison status builtins21/27.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; REA string-helpers01..04 ledgers. Near DS=SS, DF=0. BP/SI/DI preserved;
; AX/BX/CX/DX/ES/flags volatile. CRT helpers are caller-cleaned; byte/index
; and builtin reads RET, store_integer(value) RET2. All results AX.
; Comparison uses unsigned bytes, returningFFFF/0/1. Lowercase changes only
; ASCII A..Z; high bytes are preserved. Fill writes raw bytes without NUL.
; Bounded wrappers inherit native range/error-return policy; no pointer safety.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_STRING_SERVICES_FLAT
%if ASPECT_STRING_SERVICES_UNIT=1
ORG 0x9476
%elif ASPECT_STRING_SERVICES_UNIT=2
ORG 0x9be8
%elif ASPECT_STRING_SERVICES_UNIT=3
ORG 0x9736
%elif ASPECT_STRING_SERVICES_UNIT=4
ORG 0xdde3
%elif ASPECT_STRING_SERVICES_UNIT=5
ORG 0xde1c
%elif ASPECT_STRING_SERVICES_UNIT=6
ORG 0xde3a
%elif ASPECT_STRING_SERVICES_UNIT=7
ORG 0xda0c
%elif ASPECT_STRING_SERVICES_UNIT=8
ORG 0xda28
%else
%error Select ASPECT_STRING_SERVICES_UNIT1..8
%endif
%define aspect_string_bounded_integer 0xdd68
%define aspect_expr_integer_address 0xde4d
%define aspect_string_compare_result 0xd124
%else
%define ASPECT_STRING_SERVICES_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_string_strcmp
global aspect_string_lower
global aspect_string_fill
global aspect_string_byte_operand
global aspect_string_index_operand
global aspect_string_store_integer
global aspect_string_status
global aspect_string_success
extern aspect_string_bounded_integer
extern aspect_expr_integer_address
extern aspect_string_compare_result
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=1
aspect_string_strcmp:
.L9476:
 push bp
.L9477:
 mov_load bp, sp
.L9479:
 mov_load dx, di
.L947b:
 mov_load bx, si
.L947d:
 mov ax, ds
.L947f:
 mov es, ax
.L9481:
 mov si, word [bp + 0x4]
.L9484:
 mov di, word [bp + 0x6]
.L9487:
 xor_load ax, ax
.L9489:
 mov cx, 0xffff
.L948c:
 repne scasb
.L948e:
 not cx
.L9490:
 sub_load di, cx
.L9492:
 repe cmpsb
.L9494:
 jz .L949b
.L9496:
 sbb_load ax, ax
.L9498:
 sbb ax, strict word 0xffff
.L949b:
 mov_load si, bx
.L949d:
 mov_load di, dx
.L949f:
 pop bp
.L94a0:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=2
aspect_string_lower:
.L9be8:
 push bp
.L9be9:
 mov_load bp, sp
.L9beb:
 mov bx, word [bp + 0x4]
.L9bee:
 mov_load dx, bx
.L9bf0:
 jmp .L9bfd
.L9bf2:
 sub al, 0x41
.L9bf4:
 cmp al, 0x1a
.L9bf6:
 jnc .L9bfc
.L9bf8:
 add al, 0x61
.L9bfa:
 mov byte [bx], al
.L9bfc:
 inc bx
.L9bfd:
 mov al, byte [bx]
.L9bff:
 or_load al, al
.L9c01:
 jnz .L9bf2
.L9c03:
 xchg ax, dx
.L9c04:
 pop bp
.L9c05:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=3
aspect_string_fill:
.L9736:
 push bp
.L9737:
 mov_load bp, sp
.L9739:
 mov_load dx, di
.L973b:
 mov ax, ds
.L973d:
 mov es, ax
.L973f:
 mov di, word [bp + 0x4]
.L9742:
 mov_load bx, di
.L9744:
 mov cx, word [bp + 0x8]
.L9747:
 jcxz .L975e
.L9749:
 mov al, byte [bp + 0x6]
.L974c:
 mov_load ah, al
.L974e:
 test di, 0x1
.L9752:
 jz .L9756
.L9754:
 stosb
.L9755:
 dec cx
.L9756:
 shr cx, 0x1
.L9758:
 rep stosw
.L975a:
 adc_load cx, cx
.L975c:
 rep stosb
.L975e:
 mov_load di, dx
.L9760:
 xchg ax, bx
.L9761:
 pop bp
.L9762:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=4
aspect_string_byte_operand:
.Ldde3:
 sub_load ax, ax
.Ldde5:
 push ax
.Ldde6:
 mov ax, 0xff
.Ldde9:
 push ax
.Lddea:
 call aspect_string_bounded_integer
.Ldded:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=5
aspect_string_index_operand:
.Lde1c:
 sub_load ax, ax
.Lde1e:
 push ax
.Lde1f:
 mov ax, 0x4f
.Lde22:
 push ax
.Lde23:
 call aspect_string_bounded_integer
.Lde26:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=6
aspect_string_store_integer:
.Lde3a:
 push bp
.Lde3b:
 mov_load bp, sp
.Lde3d:
 call aspect_expr_integer_address
.Lde40:
 mov_load bx, ax
.Lde42:
 mov ax, word [bp + 0x4]
.Lde45:
 mov word [bx], ax
.Lde47:
 mov_load sp, bp
.Lde49:
 pop bp
.Lde4a:
 ret 0x2
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=7
aspect_string_status:
.Lda0c:
 mov ax, [aspect_string_compare_result]
.Lda0f:
 ret
%endif
%if ASPECT_STRING_SERVICES_UNIT=0 || ASPECT_STRING_SERVICES_UNIT=8
aspect_string_success:
.Lda28:
 cmp word [aspect_string_compare_result], 0x1
.Lda2d:
 sbb_load ax, ax
.Lda2f:
 neg ax
.Lda31:
 ret
%endif
