; Exact PCPlus2.01 string operands, scratch/global ownership, literal decoding,
; bounded length operand and assignment. Original SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Recovered REA string01..03 ledgers, retained anchored16/17 listings.
; Near DS=SS, DF=0; BP/SI/DI preserved. ES/AX/BX/CX/DX/flags volatile.
; read_indexed(flag) RET2; read_global(flag,index) RET4; bounded_integer(upper,
; lower) RET4; far_copy(srcseg,srcoff,dstseg,dstoff,length) caller cleanup.
; Other entries RET. Reads return nearAX. Global strings use actual far pointers;
; destination read records a scratch writeback, flush copies81bytes and clears it.
; Eleven81-byte scratch slots rotate modulo11. Literal length/key/index/frame
; arithmetic is native unchecked16-bit. Partial/EOF reads require external abort.
; Builtin string service and native error policy are explicit dependencies.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_STRING_FLAT
%if ASPECT_STRING_UNIT=1
ORG 0xdf04
%elif ASPECT_STRING_UNIT=2
ORG 0xdd68
%elif ASPECT_STRING_UNIT=3
ORG 0xde11
%elif ASPECT_STRING_UNIT=4
ORG 0xe0e4
%elif ASPECT_STRING_UNIT=5
ORG 0x9286
%elif ASPECT_STRING_UNIT=6
ORG 0x76b0
%elif ASPECT_STRING_UNIT=7
ORG 0xeef0
%elif ASPECT_STRING_UNIT=8
ORG 0xef1d
%else
%error Select ASPECT_STRING_UNIT1..8
%endif
%define native_string_read 0xdf04
%define native_string_read_destination 0xdf0b
%define native_string_read_indexed 0xdf13
%define native_string_read_global 0xdf71
%define native_string_next_scratch 0xdfc7
%define native_string_read_literal 0xdfea
%define native_string_flush 0xe0a4
%define native_string_bounded_integer 0xdd68
%define native_string_length_operand 0xde11
%define native_string_option_flag 0xe0e4
%define native_string_far_copy 0x9286
%define native_string_get_ds 0x76b0
%define native_string_copy_count 0xeef0
%define native_string_assign 0xef1d
%define aspect_operand_next_token 0xe0f1
%define aspect_dispatch_read 0x4cb4
%define aspect_operand_invalid 0x4f90
%define aspect_string_builtin 0xda83
%define aspect_operand_frame_minus 0xd1a6
%define aspect_operand_frame_plus 0xd19e
%define aspect_flow_fread 0x845a
%define aspect_string_error 0x4efb
%define aspect_operand_read_integer 0xdc48
%define erase_move_bytes 0x85b4
%define aspect_string_bank_a 0xd13a
%define aspect_globals_table 0xdb82
%define aspect_string_pending_far 0xdd82
%define aspect_string_pending_near 0xdd86
%define aspect_string_scratch 0xdd88
%define aspect_string_scratch_pointer 0xe104
%define aspect_string_scratch_index 0xe106
%define aspect_string_transform 0x7748
%define aspect_flow_stream 0x4b02
%define aspect_string_check_range 0xe37c
%define aspect_dispatch_exit_state 0xe378
%else
%define ASPECT_STRING_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_string_read
%define native_string_read aspect_string_read
global aspect_string_read_destination
%define native_string_read_destination aspect_string_read_destination
global aspect_string_read_indexed
%define native_string_read_indexed aspect_string_read_indexed
global aspect_string_read_global
%define native_string_read_global aspect_string_read_global
global aspect_string_next_scratch
%define native_string_next_scratch aspect_string_next_scratch
global aspect_string_read_literal
%define native_string_read_literal aspect_string_read_literal
global aspect_string_flush
%define native_string_flush aspect_string_flush
global aspect_string_bounded_integer
%define native_string_bounded_integer aspect_string_bounded_integer
global aspect_string_length_operand
%define native_string_length_operand aspect_string_length_operand
global aspect_string_option_flag
%define native_string_option_flag aspect_string_option_flag
global aspect_string_far_copy
%define native_string_far_copy aspect_string_far_copy
global aspect_string_get_ds
%define native_string_get_ds aspect_string_get_ds
global aspect_string_copy_count
%define native_string_copy_count aspect_string_copy_count
global aspect_string_assign
%define native_string_assign aspect_string_assign
extern aspect_flow_fread
extern aspect_string_error
extern aspect_globals_table
extern aspect_string_pending_far
extern aspect_string_check_range
extern aspect_dispatch_exit_state
extern aspect_string_builtin
extern aspect_operand_frame_minus
extern aspect_string_pending_near
extern aspect_string_scratch_pointer
extern aspect_operand_invalid
extern aspect_string_scratch_index
extern erase_move_bytes
extern aspect_string_transform
extern aspect_operand_frame_plus
extern aspect_string_bank_a
extern aspect_dispatch_read
extern aspect_operand_read_integer
extern aspect_flow_stream
extern aspect_string_scratch
extern aspect_operand_next_token
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=1
aspect_string_read:
.Ldf04:
 sub_load ax, ax
.Ldf06:
 push ax
.Ldf07:
 call native_string_read_indexed
.Ldf0a:
 ret
aspect_string_read_destination:
.Ldf0b:
 mov ax, 0x1
.Ldf0e:
 push ax
.Ldf0f:
 call native_string_read_indexed
.Ldf12:
 ret
aspect_string_read_indexed:
.Ldf13:
 push bp
.Ldf14:
 mov_load bp, sp
.Ldf16:
 call aspect_operand_next_token
.Ldf19:
 sub ax, strict word 0x64
.Ldf1c:
 jz .Ldf3c
.Ldf1e:
 sub ax, strict word 0xa
.Ldf21:
 jz .Ldf49
.Ldf23:
 sub ax, strict word 0x1e
.Ldf26:
 jz .Ldf52
.Ldf28:
 sub ax, strict word 0xa
.Ldf2b:
 jz .Ldf5e
.Ldf2d:
 sub ax, strict word 0xa
.Ldf30:
 jz .Ldf63
.Ldf32:
 sub ax, strict word 0xa
.Ldf35:
 jz .Ldf68
.Ldf37:
 call aspect_operand_invalid
.Ldf3a:
 jmp .Ldf6b
.Ldf3c:
 call aspect_dispatch_read
.Ldf3f:
 mov cx, 0x51
.Ldf42:
 imul cx
.Ldf44:
 add ax, aspect_string_bank_a
.Ldf47:
 jmp .Ldf6b
.Ldf49:
 call aspect_dispatch_read
.Ldf4c:
 push ax
.Ldf4d:
 call aspect_string_builtin
.Ldf50:
 jmp .Ldf6b
.Ldf52:
 call aspect_dispatch_read
.Ldf55:
 push ax
.Ldf56:
 push word [bp + 0x4]
.Ldf59:
 call native_string_read_global
.Ldf5c:
 jmp .Ldf6b
.Ldf5e:
 call aspect_operand_frame_minus
.Ldf61:
 jmp .Ldf6b
.Ldf63:
 call aspect_operand_frame_plus
.Ldf66:
 jmp .Ldf6b
.Ldf68:
 call native_string_read_literal
.Ldf6b:
 mov_load sp, bp
.Ldf6d:
 pop bp
.Ldf6e:
 ret 0x2
aspect_string_read_global:
.Ldf71:
 push bp
.Ldf72:
 mov_load bp, sp
.Ldf74:
 sub sp, 0x4
.Ldf77:
 push si
.Ldf78:
 mov bx, word [bp + 0x6]
.Ldf7b:
 shl bx, 0x1
.Ldf7d:
 shl bx, 0x1
.Ldf7f:
 mov ax, word [bx + aspect_globals_table]
.Ldf83:
 mov dx, word [bx + aspect_globals_table+2]
.Ldf87:
 mov word [bp + -0x4], ax
.Ldf8a:
 mov word [bp + -0x2], dx
.Ldf8d:
 call native_string_next_scratch
.Ldf90:
 mov_load si, ax
.Ldf92:
 cmp word [bp + 0x4], 0x0
.Ldf96:
 jz .Ldfa9
.Ldf98:
 mov ax, word [bp + -0x4]
.Ldf9b:
 mov dx, word [bp + -0x2]
.Ldf9e:
 mov [aspect_string_pending_far], ax
.Ldfa1:
 mov word [aspect_string_pending_far+2], dx
.Ldfa5:
 mov word [aspect_string_pending_near], si
.Ldfa9:
 mov ax, 0x51
.Ldfac:
 push ax
.Ldfad:
 push si
.Ldfae:
 call native_string_get_ds
.Ldfb1:
 push ax
.Ldfb2:
 push word [bp + -0x4]
.Ldfb5:
 push word [bp + -0x2]
.Ldfb8:
 call native_string_far_copy
.Ldfbb:
 add sp, 0xa
.Ldfbe:
 mov_load ax, si
.Ldfc0:
 pop si
.Ldfc1:
 mov_load sp, bp
.Ldfc3:
 pop bp
.Ldfc4:
 ret 0x4
aspect_string_next_scratch:
.Ldfc7:
 mov ax, 0x51
.Ldfca:
 mul word [aspect_string_scratch_index]
.Ldfce:
 add ax, aspect_string_scratch
.Ldfd1:
 mov [aspect_string_scratch_pointer], ax
.Ldfd4:
 inc word [aspect_string_scratch_index]
.Ldfd8:
 mov cx, 0xb
.Ldfdb:
 mov ax, [aspect_string_scratch_index]
.Ldfde:
 sub_load dx, dx
.Ldfe0:
 div cx
.Ldfe2:
 mov word [aspect_string_scratch_index], dx
.Ldfe6:
 mov ax, [aspect_string_scratch_pointer]
.Ldfe9:
 ret
aspect_string_read_literal:
.Ldfea:
 push bp
.Ldfeb:
 mov_load bp, sp
.Ldfed:
 sub sp, 0x18
.Ldff0:
 push di
.Ldff1:
 push si
.Ldff2:
 call native_string_next_scratch
.Ldff5:
 mov word [bp + -0xa], ax
.Ldff8:
 call aspect_dispatch_read
.Ldffb:
 mov_load cx, ax
.Ldffd:
 mov al, [aspect_string_transform]
.Le000:
 cbw
.Le001:
 mov_load dx, ax
.Le003:
 mov_load ax, cx
.Le005:
 sub_load ax, dx
.Le007:
 mov cx, 0x100
.Le00a:
 cwd
.Le00b:
 idiv cx
.Le00d:
 mov word [bp + -0x6], dx
.Le010:
 call aspect_dispatch_read
.Le013:
 mov word [bp + -0x8], ax
.Le016:
 push word [aspect_flow_stream]
.Le01a:
 push word [bp + -0x6]
.Le01d:
 mov ax, 0x1
.Le020:
 push ax
.Le021:
 push word [bp + -0xa]
.Le024:
 call aspect_flow_fread
.Le027:
 add sp, 0x8
.Le02a:
 mov al, byte [bp + -0x8]
.Le02d:
 and ax, 0x80
.Le030:
 cmp ax, strict word 0x1
.Le033:
 sbb_load ax, ax
.Le035:
 inc ax
.Le036:
 mov word [bp + -0x4], ax
.Le039:
 mov word [bp + -0x2], 0x0
.Le03e:
 mov si, word [bp + -0x2]
.Le041:
 jmp .Le05e
.Le043:
 mov al, byte [bp + -0x4]
.Le046:
 mov_load cx, si
.Le048:
 add_load al, cl
.Le04a:
 test al, 0x1
.Le04c:
 jz .Le054
.Le04e:
 mov al, byte [si + aspect_string_transform]
.Le052:
 jmp .Le05a
.Le054:
 mov al, byte [si + aspect_string_transform]
.Le058:
 neg al
.Le05a:
 mov byte [bp + si + -0x18], al
.Le05d:
 inc si
.Le05e:
 cmp si, 0xd
.Le061:
 jc .Le043
.Le063:
 mov al, byte [bp + -0x8]
.Le066:
 and ax, strict word 0x7f
.Le069:
 sub ax, word [bp + -0x6]
.Le06c:
 mov word [bp + -0x2], ax
.Le06f:
 sub_load si, si
.Le071:
 mov di, word [bp + -0xa]
.Le074:
 jmp .Le08e
.Le076:
 add si, word [bp + -0x2]
.Le079:
 mov_load ax, si
.Le07b:
 mov cx, 0xd
.Le07e:
 sub_load dx, dx
.Le080:
 div cx
.Le082:
 mov_load bx, dx
.Le084:
 lea ax, [bp + -0x18]
.Le087:
 add_load bx, ax
.Le089:
 mov al, byte [bx]
.Le08b:
 add byte [di], al
.Le08d:
 inc di
.Le08e:
 mov ax, word [bp + -0x6]
.Le091:
 dec word [bp + -0x6]
.Le094:
 or_load ax, ax
.Le096:
 jnz .Le076
.Le098:
 mov byte [di], 0x0
.Le09b:
 mov ax, [aspect_string_scratch_pointer]
.Le09e:
 pop si
.Le09f:
 pop di
.Le0a0:
 mov_load sp, bp
.Le0a2:
 pop bp
.Le0a3:
 ret
aspect_string_flush:
.Le0a4:
 cmp word [aspect_string_pending_near], 0x0
.Le0a9:
 jz .Le0cb
.Le0ab:
 mov ax, 0x51
.Le0ae:
 push ax
.Le0af:
 push word [aspect_string_pending_far]
.Le0b3:
 push word [aspect_string_pending_far+2]
.Le0b7:
 push word [aspect_string_pending_near]
.Le0bb:
 call native_string_get_ds
.Le0be:
 push ax
.Le0bf:
 call native_string_far_copy
.Le0c2:
 add sp, 0xa
.Le0c5:
 mov word [aspect_string_pending_near], 0x0
.Le0cb:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=2
aspect_string_bounded_integer:
.Ldd68:
 push bp
.Ldd69:
 mov_load bp, sp
.Ldd6b:
 push si
.Ldd6c:
 call aspect_operand_read_integer
.Ldd6f:
 mov_load si, ax
.Ldd71:
 cmp word [aspect_string_check_range], 0x0
.Ldd76:
 jz .Ldd93
.Ldd78:
 cmp word [bp + 0x4], si
.Ldd7b:
 jl .Ldd82
.Ldd7d:
 cmp word [bp + 0x6], si
.Ldd80:
 jle .Ldd93
.Ldd82:
 mov ax, 0x1
.Ldd85:
 push ax
.Ldd86:
 call aspect_string_error
.Ldd89:
 cmp word [aspect_dispatch_exit_state], 0x0
.Ldd8e:
 jz .Ldd93
.Ldd90:
 mov si, word [bp + 0x6]
.Ldd93:
 mov_load ax, si
.Ldd95:
 pop si
.Ldd96:
 mov_load sp, bp
.Ldd98:
 pop bp
.Ldd99:
 ret 0x4
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=3
aspect_string_length_operand:
.Lde11:
 sub_load ax, ax
.Lde13:
 push ax
.Lde14:
 mov ax, 0x50
.Lde17:
 push ax
.Lde18:
 call native_string_bounded_integer
.Lde1b:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=4
aspect_string_option_flag:
.Le0e4:
 call aspect_dispatch_read
.Le0e7:
 dec ax
.Le0e8:
 jnz .Le0ee
.Le0ea:
 mov ax, 0x1
.Le0ed:
 ret
.Le0ee:
 sub_load ax, ax
.Le0f0:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=5
aspect_string_far_copy:
.L9286:
 push bp
.L9287:
 mov_load bp, sp
.L9289:
 push si
.L928a:
 push di
.L928b:
 push ds
.L928c:
 mov ds, word [bp + 0x4]
.L928f:
 mov si, word [bp + 0x6]
.L9292:
 mov es, word [bp + 0x8]
.L9295:
 mov di, word [bp + 0xa]
.L9298:
 mov cx, word [bp + 0xc]
.L929b:
 rep movsb
.L929d:
 pop ds
.L929e:
 pop di
.L929f:
 pop si
.L92a0:
 mov_load sp, bp
.L92a2:
 pop bp
.L92a3:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=6
aspect_string_get_ds:
.L76b0:
 mov ax, ds
.L76b2:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=7
aspect_string_copy_count:
.Leef0:
 call native_string_option_flag
.Leef3:
 or_load ax, ax
.Leef5:
 jz .Leefb
.Leef7:
 call native_string_length_operand
.Leefa:
 ret
.Leefb:
 mov ax, 0x50
.Leefe:
 ret
%endif
%if ASPECT_STRING_UNIT=0 || ASPECT_STRING_UNIT=8
aspect_string_assign:
.Lef1d:
 push di
.Lef1e:
 push si
.Lef1f:
 call native_string_read_destination
.Lef22:
 mov_load si, ax
.Lef24:
 call native_string_read
.Lef27:
 mov_load di, ax
.Lef29:
 call native_string_copy_count
.Lef2c:
 push ax
.Lef2d:
 push di
.Lef2e:
 push si
.Lef2f:
 mov_load di, ax
.Lef31:
 call erase_move_bytes
.Lef34:
 add sp, 0x6
.Lef37:
 add_load si, di
.Lef39:
 mov byte [si], 0x0
.Lef3c:
 call native_string_flush
.Lef3f:
 pop si
.Lef40:
 pop di
.Lef41:
 ret
%endif
