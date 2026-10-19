; Exact PCPlus2.01 native ASPECT EXIT/MESSAGE/PAUSE and text helpers.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Resident byte coordinates except bounded-operand DD9C in overlay16.
; DS=SS,DF=0, nearRET, BP/SI/DI preserved; AX/BX/CX/DX/ES/flags volatile.
; Decoder/source/destination and print helpers cdecl. Native wait_ticks RET2;
; pause_operand RET, bounded integer RET4. Emit_byte cdecl; cancel/wait RET.
; Resident overlay thunks CE1F/CDD7 resolve to DF04/DD9C in linked modules.
; MESSAGE uses an82-byte stack buffer, native caret decode and optionalCRLF.
; Carets: ^@ ->FF, ^^ ->1E, ^^^ ->5E. No input bounds/trailing-caret guard.
; EXIT stores1 and returns; PAUSE stores cancellation result in comparisonword.
; Native delay enables interrupts, clobbers ES=0, waits(count+1) BIOS0040:006C
; transitions with16-bit wrap; wrapped zero still waits once. IF is not preserved.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CONSOLE_FLAT
%if ASPECT_CONSOLE_UNIT=1
ORG 0x4eb5
%elif ASPECT_CONSOLE_UNIT=2
ORG 0x5029
%elif ASPECT_CONSOLE_UNIT=3
ORG 0x507b
%elif ASPECT_CONSOLE_UNIT=4
ORG 0x4934
%elif ASPECT_CONSOLE_UNIT=5
ORG 0x3abd
%elif ASPECT_CONSOLE_UNIT=6
ORG 0xdd9c
%elif ASPECT_CONSOLE_UNIT=7
ORG 0x6b98
%else
%error Select ASPECT_CONSOLE_UNIT1..7
%endif
%if ASPECT_CONSOLE_UNIT!=4
%define aspect_console_decode 0x4934
%endif
%if ASPECT_CONSOLE_UNIT!=5
%define aspect_console_print_line 0x3abd
%define aspect_console_print 0x3adb
%endif
%if ASPECT_CONSOLE_UNIT!=7
%define aspect_console_native_wait_ticks 0x6b98
%endif
%define aspect_console_read_pause 0xcdd7
%define aspect_string_read 0xce1f
%define aspect_console_cancel_poll 0x4e34
%define aspect_console_wait_second 0x6bb6
%define aspect_console_emit_byte 0x0610
%define aspect_string_bounded_integer 0xdd68
%define aspect_dispatch_exit_state 0xe378
%define aspect_console_message_mode 0xe38a
%define aspect_string_compare_result 0xd124
%else
%define aspect_console_read_pause aspect_console_pause_operand
%define ASPECT_CONSOLE_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_console_exit
global aspect_console_message
global aspect_console_pause
global aspect_console_decode
global aspect_console_print_line
global aspect_console_print
global aspect_console_pause_operand
global aspect_console_native_wait_ticks
global aspect_console_native_wait_second
extern aspect_string_read
extern aspect_console_cancel_poll
extern aspect_console_wait_second
extern aspect_console_emit_byte
extern aspect_string_bounded_integer
extern aspect_dispatch_exit_state
extern aspect_console_message_mode
extern aspect_string_compare_result
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=1
; REA ev_033eb4e9302a3d8ce9950392879d3042c32c2bc61561cbd8cd3f53cc226afa4b
aspect_console_exit:
console_loc_4eb5:
 mov word [aspect_dispatch_exit_state], 0x1
console_loc_4ebb:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=2
; REA ev_33ebbe092e348b3c506e6bd011b3ceb4d06259546103cfee79009028d9c9603f
aspect_console_message:
console_loc_5029:
 push bp
console_loc_502a:
 mov_load bp, sp
console_loc_502c:
 sub sp, 0x52
console_loc_502f:
 lea ax, [bp + -0x52]
console_loc_5032:
 push ax
console_loc_5033:
 call aspect_string_read
console_loc_5036:
 push ax
console_loc_5037:
 call aspect_console_decode
console_loc_503a:
 pop bx
console_loc_503b:
 pop bx
console_loc_503c:
 cmp word [aspect_console_message_mode], 0x0
console_loc_5041:
 jz console_loc_504c
console_loc_5043:
 lea ax, [bp + -0x52]
console_loc_5046:
 push ax
console_loc_5047:
 call aspect_console_print_line
console_loc_504a:
 jmp console_loc_5053
console_loc_504c:
 lea ax, [bp + -0x52]
console_loc_504f:
 push ax
console_loc_5050:
 call aspect_console_print
console_loc_5053:
 pop bx
console_loc_5054:
 mov_load sp, bp
console_loc_5056:
 pop bp
console_loc_5057:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=3
; REA ev_4e59c48f5fad830c9526d500eb53b97c9eb0977ef2ba35a4fb01cd61ef81257f
aspect_console_pause:
console_loc_507b:
 push bp
console_loc_507c:
 mov_load bp, sp
console_loc_507e:
 push si
console_loc_507f:
 call aspect_console_read_pause
console_loc_5082:
 mov_load si, ax
console_loc_5084:
 jmp console_loc_5090
console_loc_5086:
 call aspect_console_cancel_poll
console_loc_5089:
 or_load ax, ax
console_loc_508b:
 jnz console_loc_5097
console_loc_508d:
 call aspect_console_wait_second
console_loc_5090:
 mov_load ax, si
console_loc_5092:
 dec si
console_loc_5093:
 or_load ax, ax
console_loc_5095:
 jnz console_loc_5086
console_loc_5097:
 or_load si, si
console_loc_5099:
 jl console_loc_50a0
console_loc_509b:
 mov ax, 0x1
console_loc_509e:
 jmp console_loc_50a2
console_loc_50a0:
 sub_load ax, ax
console_loc_50a2:
 mov [aspect_string_compare_result], ax
console_loc_50a5:
 pop si
console_loc_50a6:
 mov_load sp, bp
console_loc_50a8:
 pop bp
console_loc_50a9:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=4
; REA ev_95adc82a00e4a0e4766ae1b6546ffcb0a4e81112274ad2c3be9860cc71d5500b
aspect_console_decode:
console_loc_4934:
 push bp
console_loc_4935:
 mov_load bp, sp
console_loc_4937:
 sub sp, 0x2
console_loc_493a:
 push di
console_loc_493b:
 push si
console_loc_493c:
 mov si, word [bp + 0x4]
console_loc_493f:
 mov di, word [bp + 0x6]
console_loc_4942:
 cmp byte [si], 0x0
console_loc_4945:
 jz console_loc_4982
console_loc_4947:
 mov al, byte [si]
console_loc_4949:
 mov byte [bp + -0x1], al
console_loc_494c:
 cmp al, 0x5e
console_loc_494e:
 jnz console_loc_4965
console_loc_4950:
 inc si
console_loc_4951:
 mov al, byte [si]
console_loc_4953:
 cbw
console_loc_4954:
 sub ax, strict word 0x40
console_loc_4957:
 jz console_loc_496f
console_loc_4959:
 sub ax, strict word 0x1e
console_loc_495c:
 jz console_loc_4975
console_loc_495e:
 mov al, byte [si]
console_loc_4960:
 and al, 0x1f
console_loc_4962:
 mov byte [bp + -0x1], al
console_loc_4965:
 inc si
console_loc_4966:
 mov al, byte [bp + -0x1]
console_loc_4969:
 inc di
console_loc_496a:
 mov byte [di + -0x1], al
console_loc_496d:
 jmp console_loc_4942
console_loc_496f:
 mov byte [bp + -0x1], 0xff
console_loc_4973:
 jmp console_loc_4965
console_loc_4975:
 cmp byte [si + 0x1], 0x5e
console_loc_4979:
 jnz console_loc_495e
console_loc_497b:
 mov byte [bp + -0x1], 0x5e
console_loc_497f:
 inc si
console_loc_4980:
 jmp console_loc_4965
console_loc_4982:
 mov byte [di], 0x0
console_loc_4985:
 pop si
console_loc_4986:
 pop di
console_loc_4987:
 mov_load sp, bp
console_loc_4989:
 pop bp
console_loc_498a:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=5
; REA ev_60e498def0b6aede363ed3fbe5e613e61c56b7e8ba8551294a909f572a6771bf
aspect_console_print_line:
console_loc_3abd:
 push bp
console_loc_3abe:
 mov_load bp, sp
console_loc_3ac0:
 push word [bp + 0x4]
console_loc_3ac3:
 call aspect_console_print
console_loc_3ac6:
 pop bx
console_loc_3ac7:
 mov ax, 0xd
console_loc_3aca:
 push ax
console_loc_3acb:
 call aspect_console_emit_byte
console_loc_3ace:
 pop bx
console_loc_3acf:
 mov ax, 0xa
console_loc_3ad2:
 push ax
console_loc_3ad3:
 call aspect_console_emit_byte
console_loc_3ad6:
 pop bx
console_loc_3ad7:
 mov_load sp, bp
console_loc_3ad9:
 pop bp
console_loc_3ada:
 ret
; REA ev_96e4382662bb68062ce864b541584a0e6bc95fd0cda2a29ec3a7f6e1cc2b3e43
aspect_console_print:
console_loc_3adb:
 push bp
console_loc_3adc:
 mov_load bp, sp
console_loc_3ade:
 jmp console_loc_3aec
console_loc_3ae0:
 inc word [bp + 0x4]
console_loc_3ae3:
 mov al, byte [bx]
console_loc_3ae5:
 sub_load ah, ah
console_loc_3ae7:
 push ax
console_loc_3ae8:
 call aspect_console_emit_byte
console_loc_3aeb:
 pop bx
console_loc_3aec:
 mov bx, word [bp + 0x4]
console_loc_3aef:
 cmp byte [bx], 0x0
console_loc_3af2:
 jnz console_loc_3ae0
console_loc_3af4:
 mov_load sp, bp
console_loc_3af6:
 pop bp
console_loc_3af7:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=6
; REA ev_8cdf42580163a2eecce5b217c38fd9a07b1f20e95da53882981a9bd58598de23
aspect_console_pause_operand:
console_loc_dd9c:
 sub_load ax, ax
console_loc_dd9e:
 push ax
console_loc_dd9f:
 mov ax, 0x7fff
console_loc_dda2:
 push ax
console_loc_dda3:
 call aspect_string_bounded_integer
console_loc_dda6:
 ret
%endif
%if ASPECT_CONSOLE_UNIT=0 || ASPECT_CONSOLE_UNIT=7
; REA ev_41993008d8e1d5c76aaa8819953f7fc52f280e58ebd9d142f515118f9a45fc7e
aspect_console_native_wait_ticks:
console_loc_6b98:
 mov_load bx, sp
console_loc_6b9a:
 mov dx, word [bx + 0x2]
console_loc_6b9d:
 inc dx
console_loc_6b9e:
 sti
console_loc_6b9f:
 xor_load cx, cx
console_loc_6ba1:
 mov es, cx
console_loc_6ba3:
 mov bx, 0x46c
console_loc_6ba6:
 mov ax, word es:[bx]
console_loc_6ba9:
 cmp ax, word es:[bx]
console_loc_6bac:
 jz console_loc_6ba9
console_loc_6bae:
 inc cx
console_loc_6baf:
 cmp_load cx, dx
console_loc_6bb1:
 jc console_loc_6ba6
console_loc_6bb3:
 ret 0x2
; REA ev_1abff854b02b506a5e1608cb35e70f68aab667cb4442dd6e3af895599dec3e32
aspect_console_native_wait_second:
console_loc_6bb6:
 mov ax, 0x12
console_loc_6bb9:
 push ax
console_loc_6bba:
 call aspect_console_native_wait_ticks
console_loc_6bbd:
 ret
%endif
