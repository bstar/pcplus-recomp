; Exact PCPlus2.01 overlay16 numeric selection and token primitives.
; Retained REA analysis/pcplus-overlay-anchored-16/functions/0x1d19e.asm,
; 0x1d1a6.asm,0x1db10.asm,0x1db2b.asm,0x1db48.asm,0x1dc48.asm,
; 0x1dcc1.asm,0x1e0f1.asm. Original SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS, DF=0; near ABI; predicates and builtin callbacks consume one word;
; other entries RET. Integer/address/token AX, long DX:AX. BP/SI/DI preserved;
; AX/BX/CX/DX/ES/flags volatile. Banks retain neutral names pending ownership.
; Selection and frame/index arithmetic are native unchecked16-bit operations.
; EOF can becomeFFFF, wrap a bank index or participate in a word operand.
; Nonzero lookahead is consumed verbatim; zero means absent. Invalid selector
; callback may return or unwind. Builtin/system values are explicit dependencies,
; not substitutes for recovered application services. Floating predicate only:
; floating operand/conversion routines DD26+ are not part of this module.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_OPERANDS_FLAT
%if ASPECT_OPERANDS_UNIT=1
ORG 0xd19e
%elif ASPECT_OPERANDS_UNIT=2
ORG 0xdb10
%elif ASPECT_OPERANDS_UNIT=3
ORG 0xdc48
%elif ASPECT_OPERANDS_UNIT=4
ORG 0xe0f1
%else
%error Select ASPECT_OPERANDS_UNIT1..4
%endif
%define aspect_flow_stream 0x4b02
%define aspect_flow_refill 0x9094
%define aspect_flow_read_word 0xe129
%define aspect_flow_read_dword 0xe176
%define aspect_flow_frame 0xe13a
%define aspect_dispatch_read 0x4cb4
%define aspect_operand_lookahead 0xe38c
%define aspect_operand_builtin_integer 0xd988
%define aspect_operand_builtin_long 0xda39
%define aspect_operand_invalid 0x4f90
%define aspect_operand_integer_bank_a 0xd126
%define aspect_operand_integer_bank_b 0xd482
%define aspect_operand_long_bank 0xd582
%define aspect_operand_system_values 0xe3c4
%define native_next_token 0xe0f1
%define native_frame_plus 0xd19e
%define native_frame_minus 0xd1a6
%else
%define ASPECT_OPERANDS_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_operand_is_integer,aspect_operand_is_long,aspect_operand_is_float
global aspect_operand_frame_plus,aspect_operand_frame_minus
global aspect_operand_next_token,aspect_operand_read_integer,aspect_operand_read_long
extern aspect_flow_stream,aspect_flow_refill,aspect_flow_read_word,aspect_flow_read_dword,aspect_flow_frame
extern aspect_dispatch_read,aspect_operand_lookahead,aspect_operand_builtin_integer
extern aspect_operand_builtin_long,aspect_operand_invalid
extern aspect_operand_integer_bank_a,aspect_operand_integer_bank_b,aspect_operand_long_bank,aspect_operand_system_values
%define native_next_token aspect_operand_next_token
%define native_frame_plus aspect_operand_frame_plus
%define native_frame_minus aspect_operand_frame_minus
%endif
%if ASPECT_OPERANDS_UNIT=0 || ASPECT_OPERANDS_UNIT=1
aspect_operand_frame_plus:
 call aspect_flow_read_word
 add ax,[aspect_flow_frame]
 ret
aspect_operand_frame_minus:
 call aspect_flow_read_word
 sub ax,[aspect_flow_frame]
 neg ax
 ret
%endif
%if ASPECT_OPERANDS_UNIT=0 || ASPECT_OPERANDS_UNIT=2
aspect_operand_is_integer:
 push bp
 mov_load bp,sp
 mov ax,[bp+4]
 mov cx,10
 sub_load dx,dx
 div cx
 dec dx
 jnz .false
 mov ax,1
 jmp short .done
.false:
 sub_load ax,ax
.done:
 pop bp
 ret 2
aspect_operand_is_long:
 push bp
 mov_load bp,sp
 mov ax,[bp+4]
 mov cx,10
 sub_load dx,dx
 div cx
 cmp dx,byte 2
 jnz .false
 mov ax,1
 jmp short .done
.false:
 sub_load ax,ax
.done:
 pop bp
 ret 2
aspect_operand_is_float:
 push bp
 mov_load bp,sp
 mov ax,[bp+4]
 mov cx,10
 sub_load dx,dx
 div cx
 cmp dx,byte 3
 jnz .false
 mov ax,1
 jmp short .done
.false:
 sub_load ax,ax
.done:
 pop bp
 ret 2
%endif
%if ASPECT_OPERANDS_UNIT=0 || ASPECT_OPERANDS_UNIT=3
aspect_operand_read_integer:
 call native_next_token
 sub ax,strict word 0x65
 cmp ax,strict word 0x50
 ja .invalid
 mov bx,10
 xor_load dx,dx
 div bx
 or_load dx,dx
 jnz .invalid
 shl ax,1
 xchg ax,bx
 jmp word [cs:bx+.table]
.table:
 dw .bank_a,.builtin,.system,.invalid,.bank_b,.frame_minus,.frame_plus,.word,.byte
.invalid:
 call aspect_operand_invalid
 jmp short .done
.bank_a:
 call aspect_dispatch_read
 mov_load bx,ax
 shl bx,1
 mov ax,[bx+aspect_operand_integer_bank_a]
 jmp short .done
.builtin:
 call aspect_dispatch_read
 push ax
 call aspect_operand_builtin_integer
 ret
.system:
 call aspect_dispatch_read
 mov_load bx,ax
 mov cl,3
 shl bx,cl
 mov ax,[bx+aspect_operand_system_values]
 ret
.bank_b:
 call aspect_dispatch_read
 mov_load bx,ax
 shl bx,1
 mov ax,[bx+aspect_operand_integer_bank_b]
 ret
.frame_minus:
 call native_frame_minus
.value:
 mov_load bx,ax
 mov ax,[bx]
 ret
.frame_plus:
 call native_frame_plus
 jmp short .value
.word:
 call aspect_flow_read_word
 ret
.byte:
 call aspect_dispatch_read
.done:
 ret
aspect_operand_read_long:
 call native_next_token
 sub ax,strict word 0x70
 jz .builtin
 sub ax,strict word 10
 jz .system
 sub ax,strict word 20
 jz .bank
 sub ax,strict word 10
 jz .frame_minus
 sub ax,strict word 10
 jz .frame_plus
 sub ax,strict word 10
 jz .literal
 call aspect_operand_invalid
 ret
.builtin:
 call aspect_dispatch_read
 push ax
 call aspect_operand_builtin_long
 ret
.system:
 call aspect_dispatch_read
 mov_load bx,ax
 mov cl,3
 shl bx,cl
 mov ax,[bx+aspect_operand_system_values]
 mov dx,[bx+aspect_operand_system_values+2]
 ret
.bank:
 call aspect_dispatch_read
 mov_load bx,ax
 shl bx,1
 shl bx,1
 mov ax,[bx+aspect_operand_long_bank]
 mov dx,[bx+aspect_operand_long_bank+2]
 ret
.frame_minus:
 call native_frame_minus
.value:
 mov_load bx,ax
 mov ax,[bx]
 mov dx,[bx+2]
 ret
.frame_plus:
 call native_frame_plus
 jmp short .value
.literal:
 call aspect_flow_read_dword
 ret
%endif
%if ASPECT_OPERANDS_UNIT=0 || ASPECT_OPERANDS_UNIT=4
aspect_operand_next_token:
 push si
 cmp word [aspect_operand_lookahead],byte 0
 jne .saved
 mov bx,[aspect_flow_stream]
 dec word [bx+2]
 mov bx,[aspect_flow_stream]
 cmp word [bx+2],byte 0
 jl .refill
 mov si,[bx]
 inc word [bx]
 mov al,[si]
 sub_load ah,ah
 pop si
 ret
.refill:
 push bx
 call aspect_flow_refill
 pop bx
 pop si
 ret
.saved:
 mov dx,[aspect_operand_lookahead]
 mov word [aspect_operand_lookahead],0
 mov_load ax,dx
 pop si
 ret
%endif
