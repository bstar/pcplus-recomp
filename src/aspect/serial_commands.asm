; Exact PCPlus2.01 native ASPECT TRANSMIT/WAITFOR and text/timeout helpers.
; OriginalSHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS,DF=0,nearRET,BP/SI/DI preserved;AX/BX/CX/DX/ES/flags volatile.
; transmit/send_formatted/upper_byte use cdecl; receive/send_byte/pause_ticks/
; character_delay consume one word RET2. Native clock enables IF and setsES0.
; WAITFOR uses original prefix-only fallback,82-byte bursts and18ticks/second;
; timeout compares signed32-bit dayclock with original0x1800B0 day wrap.
; Timeout option absent/!=1 means30; explicitEND1A means0(indefinite).
; Caret FF emitsNUL without echo/delay; configured pausecharacter takes priority.
; No bounds/trailing-caret/device/flowcontrol guarantees are added here.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SERIAL_COMMANDS_FLAT
%if ASPECT_SERIAL_COMMANDS_UNIT=1
ORG 0x5176
%elif ASPECT_SERIAL_COMMANDS_UNIT=2
ORG 0x5188
%elif ASPECT_SERIAL_COMMANDS_UNIT=3
ORG 0x48cc
%elif ASPECT_SERIAL_COMMANDS_UNIT=4
ORG 0xe9f5
%elif ASPECT_SERIAL_COMMANDS_UNIT=5
ORG 0x8252
%elif ASPECT_SERIAL_COMMANDS_UNIT=6
ORG 0x77fe
%elif ASPECT_SERIAL_COMMANDS_UNIT=7
ORG 0xda32
%else
%error Select ASPECT_SERIAL_COMMANDS_UNIT1..7
%endif
%define aspect_string_read 0xce1f
%define aspect_console_decode 0x4934
%define aspect_string_upper 0x9128
%define aspect_serial_clock 0x77fe
%define aspect_serial_receive 0x4c3c
%define aspect_console_cancel_poll 0x4e34
%define aspect_string_option_flag 0xe0e4
%define aspect_dispatch_read 0x4cb4
%define aspect_string_bounded_integer 0xdd68
%define aspect_serial_send_byte 0xab0b
%define aspect_serial_pause_ticks 0x6b98
%define aspect_serial_character_delay 0x6b72
%define aspect_console_emit_byte 0x0610
%define aspect_serial_case_sensitive 0xe396
%define aspect_serial_wait_result 0xe39a
%define aspect_serial_rx_count 0x8e20
%define aspect_operand_lookahead 0xe38c
%define aspect_serial_ctype 0x7caf
%define aspect_serial_pause_character 0x1d66
%define aspect_serial_local_echo 0x1d1a
%define aspect_serial_character_delay_value 0x1d68
%if ASPECT_SERIAL_COMMANDS_UNIT!=1
%define aspect_serial_transmit 0x5176
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT!=2
%define aspect_serial_wait_for 0x5188
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT!=3
%define aspect_serial_send_formatted 0x48cc
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT!=4
%define aspect_serial_timeout_operand 0xe9f5
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT!=5
%define aspect_serial_upper_byte 0x8252
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT!=6
%define aspect_serial_native_clock 0x77fe
%endif
%define aspect_serial_read_timeout 0xcd83
%else
%define ASPECT_SERIAL_COMMANDS_UNIT 0
%define aspect_serial_read_timeout aspect_serial_timeout_operand
SEGMENT _TEXT public class=CODE use16
global aspect_serial_transmit
global aspect_serial_wait_for
global aspect_serial_send_formatted
global aspect_serial_timeout_operand
global aspect_serial_upper_byte
global aspect_serial_wait_status
global aspect_serial_native_clock
extern aspect_string_read
extern aspect_console_decode
extern aspect_string_upper
extern aspect_serial_clock
extern aspect_serial_receive
extern aspect_console_cancel_poll
extern aspect_string_option_flag
extern aspect_dispatch_read
extern aspect_string_bounded_integer
extern aspect_serial_send_byte
extern aspect_serial_pause_ticks
extern aspect_serial_character_delay
extern aspect_console_emit_byte
extern aspect_serial_case_sensitive
extern aspect_serial_wait_result
extern aspect_serial_rx_count
extern aspect_operand_lookahead
extern aspect_serial_ctype
extern aspect_serial_pause_character
extern aspect_serial_local_echo
extern aspect_serial_character_delay_value
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=1
; REA ev_87cf2aa105aee42dd19f33bb860cf8e12cfe272ad0f9fbda8f52bb77a67ceb4c
aspect_serial_transmit:
serial_loc_5176:
 call aspect_string_read
serial_loc_5179:
 push ax
serial_loc_517a:
 call aspect_serial_send_formatted
serial_loc_517d:
 pop bx
serial_loc_517e:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=2
; REA ev_d842b37298e575ef269f7fb6e054ede810352ef0b29f4fb952bba6a44661b89a
aspect_serial_wait_for:
serial_loc_5188:
 push bp
serial_loc_5189:
 mov_load bp, sp
serial_loc_518b:
 sub sp, 0x64
serial_loc_518e:
 push di
serial_loc_518f:
 push si
serial_loc_5190:
 lea ax, [bp + -0x64]
serial_loc_5193:
 mov word [bp + -0xe], ax
serial_loc_5196:
 push ax
serial_loc_5197:
 call aspect_string_read
serial_loc_519a:
 push ax
serial_loc_519b:
 call aspect_console_decode
serial_loc_519e:
 pop bx
serial_loc_519f:
 pop bx
serial_loc_51a0:
 cmp word [aspect_serial_case_sensitive], 0x0
serial_loc_51a5:
 jnz serial_loc_51af
serial_loc_51a7:
 lea ax, [bp + -0x64]
serial_loc_51aa:
 push ax
serial_loc_51ab:
 call aspect_string_upper
serial_loc_51ae:
 pop bx
serial_loc_51af:
 call aspect_serial_read_timeout
serial_loc_51b2:
 mov word [bp + -0x12], ax
serial_loc_51b5:
 or_load ax, ax
serial_loc_51b7:
 jz serial_loc_51f5
serial_loc_51b9:
 mov word [bp + -0x10], 0x0
serial_loc_51be:
 call aspect_serial_clock
serial_loc_51c1:
 mov word [bp + -0xc], ax
serial_loc_51c4:
 mov word [bp + -0xa], dx
serial_loc_51c7:
 mov_load cx, ax
serial_loc_51c9:
 mov ax, 0x12
serial_loc_51cc:
 mov_load bx, dx
serial_loc_51ce:
 imul word [bp + -0x12]
serial_loc_51d1:
 add_load ax, cx
serial_loc_51d3:
 adc_load dx, bx
serial_loc_51d5:
 mov word [bp + -0x8], ax
serial_loc_51d8:
 mov word [bp + -0x6], dx
serial_loc_51db:
 cmp dx, 0x18
serial_loc_51de:
 jl serial_loc_51f5
serial_loc_51e0:
 jg serial_loc_51e7
serial_loc_51e2:
 cmp ax, 0xb0
serial_loc_51e5:
 jbe serial_loc_51f5
serial_loc_51e7:
 sub word [bp + -0x8], 0xb0
serial_loc_51ec:
 sbb word [bp + -0x6], 0x18
serial_loc_51f0:
 mov word [bp + -0x10], 0x1
serial_loc_51f5:
 mov di, word [bp + -0xe]
serial_loc_51f8:
 cmp word [aspect_serial_rx_count], 0x0
serial_loc_51fd:
 jz serial_loc_5247
serial_loc_51ff:
 mov word [bp + -0x2], 0x51
serial_loc_5204:
 sub_load ax, ax
serial_loc_5206:
 push ax
serial_loc_5207:
 call aspect_serial_receive
serial_loc_520a:
 mov_load si, ax
serial_loc_520c:
 cmp word [aspect_serial_case_sensitive], 0x0
serial_loc_5211:
 jnz serial_loc_521a
serial_loc_5213:
 push si
serial_loc_5214:
 call aspect_serial_upper_byte
serial_loc_5217:
 pop bx
serial_loc_5218:
 mov_load si, ax
serial_loc_521a:
 mov al, byte [di]
serial_loc_521c:
 inc di
serial_loc_521d:
 sub_load ah, ah
serial_loc_521f:
 cmp_load ax, si
serial_loc_5221:
 jz serial_loc_5231
serial_loc_5223:
 lea di, [bp + -0x64]
serial_loc_5226:
 mov al, byte [di]
serial_loc_5228:
 sub_load ah, ah
serial_loc_522a:
 cmp_load ax, si
serial_loc_522c:
 jnz serial_loc_5231
serial_loc_522e:
 lea di, [bp + -0x63]
serial_loc_5231:
 cmp word [aspect_serial_rx_count], 0x0
serial_loc_5236:
 jz serial_loc_5247
serial_loc_5238:
 mov ax, word [bp + -0x2]
serial_loc_523b:
 dec word [bp + -0x2]
serial_loc_523e:
 or_load ax, ax
serial_loc_5240:
 jz serial_loc_5247
serial_loc_5242:
 cmp byte [di], 0x0
serial_loc_5245:
 jnz serial_loc_5204
serial_loc_5247:
 cmp word [bp + -0x12], 0x0
serial_loc_524b:
 jz serial_loc_52b1
serial_loc_524d:
 call aspect_serial_clock
serial_loc_5250:
 mov word [bp + -0x4], ax
serial_loc_5253:
 mov word [bp + -0x2], dx
serial_loc_5256:
 cmp word [bp + -0x10], 0x0
serial_loc_525a:
 jnz serial_loc_5282
serial_loc_525c:
 mov ax, word [bp + -0x8]
serial_loc_525f:
 mov dx, word [bp + -0x6]
serial_loc_5262:
 cmp word [bp + -0x2], dx
serial_loc_5265:
 jg serial_loc_52a6
serial_loc_5267:
 jl serial_loc_526e
serial_loc_5269:
 cmp word [bp + -0x4], ax
serial_loc_526c:
 jnc serial_loc_52a6
serial_loc_526e:
 mov ax, word [bp + -0xc]
serial_loc_5271:
 mov dx, word [bp + -0xa]
serial_loc_5274:
 cmp word [bp + -0x2], dx
serial_loc_5277:
 jl serial_loc_52a6
serial_loc_5279:
 jg serial_loc_52ab
serial_loc_527b:
 cmp word [bp + -0x4], ax
serial_loc_527e:
 jc serial_loc_52a6
serial_loc_5280:
 jmp serial_loc_52ab
serial_loc_5282:
 mov ax, word [bp + -0xc]
serial_loc_5285:
 mov dx, word [bp + -0xa]
serial_loc_5288:
 cmp word [bp + -0x2], dx
serial_loc_528b:
 jg serial_loc_52ab
serial_loc_528d:
 jl serial_loc_5294
serial_loc_528f:
 cmp word [bp + -0x4], ax
serial_loc_5292:
 jnc serial_loc_52ab
serial_loc_5294:
 mov ax, word [bp + -0x8]
serial_loc_5297:
 mov dx, word [bp + -0x6]
serial_loc_529a:
 cmp word [bp + -0x2], dx
serial_loc_529d:
 jl serial_loc_52ab
serial_loc_529f:
 jg serial_loc_52a6
serial_loc_52a1:
 cmp word [bp + -0x4], ax
serial_loc_52a4:
 jc serial_loc_52ab
serial_loc_52a6:
 mov dx, 0x1
serial_loc_52a9:
 jmp serial_loc_52ad
serial_loc_52ab:
 sub_load dx, dx
serial_loc_52ad:
 or_load dx, dx
serial_loc_52af:
 jnz serial_loc_52c0
serial_loc_52b1:
 cmp byte [di], 0x0
serial_loc_52b4:
 jz serial_loc_52c0
serial_loc_52b6:
 call aspect_console_cancel_poll
serial_loc_52b9:
 or_load ax, ax
serial_loc_52bb:
 jnz serial_loc_52c0
serial_loc_52bd:
 jmp serial_loc_51f8
serial_loc_52c0:
 cmp byte [di], 0x1
serial_loc_52c3:
 sbb_load ax, ax
serial_loc_52c5:
 neg ax
serial_loc_52c7:
 mov [aspect_serial_wait_result], ax
serial_loc_52ca:
 pop si
serial_loc_52cb:
 pop di
serial_loc_52cc:
 mov_load sp, bp
serial_loc_52ce:
 pop bp
serial_loc_52cf:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=3
; REA ev_0080ce7fa165e628068271f7e46827a2dcc3be32147195056f85b7c8cff237cc
aspect_serial_send_formatted:
serial_loc_48cc:
 push bp
serial_loc_48cd:
 mov_load bp, sp
serial_loc_48cf:
 sub sp, 0x82
serial_loc_48d3:
 push si
serial_loc_48d4:
 lea ax, [bp + 0xff7e]
serial_loc_48d8:
 push ax
serial_loc_48d9:
 push word [bp + 0x4]
serial_loc_48dc:
 call aspect_console_decode
serial_loc_48df:
 pop bx
serial_loc_48e0:
 pop bx
serial_loc_48e1:
 lea si, [bp + 0xff7e]
serial_loc_48e5:
 jmp serial_loc_4927
serial_loc_48e7:
 mov al, [aspect_serial_pause_character]
serial_loc_48ea:
 cmp byte [bp + -0x1], al
serial_loc_48ed:
 jnz serial_loc_48f8
serial_loc_48ef:
 mov ax, 0x9
serial_loc_48f2:
 push ax
serial_loc_48f3:
 call aspect_serial_pause_ticks
serial_loc_48f6:
 jmp serial_loc_4927
serial_loc_48f8:
 cmp byte [bp + -0x1], 0xff
serial_loc_48fc:
 jnz serial_loc_4906
serial_loc_48fe:
 sub_load ax, ax
serial_loc_4900:
 push ax
serial_loc_4901:
 call aspect_serial_send_byte
serial_loc_4904:
 jmp serial_loc_4927
serial_loc_4906:
 cmp word [aspect_serial_local_echo], 0x0
serial_loc_490b:
 jz serial_loc_4917
serial_loc_490d:
 mov al, byte [bp + -0x1]
serial_loc_4910:
 sub_load ah, ah
serial_loc_4912:
 push ax
serial_loc_4913:
 call aspect_console_emit_byte
serial_loc_4916:
 pop bx
serial_loc_4917:
 mov al, byte [bp + -0x1]
serial_loc_491a:
 sub_load ah, ah
serial_loc_491c:
 push ax
serial_loc_491d:
 call aspect_serial_send_byte
serial_loc_4920:
 push word [aspect_serial_character_delay_value]
serial_loc_4924:
 call aspect_serial_character_delay
serial_loc_4927:
 lodsb
serial_loc_4928:
 mov byte [bp + -0x1], al
serial_loc_492b:
 or_load al, al
serial_loc_492d:
 jnz serial_loc_48e7
serial_loc_492f:
 pop si
serial_loc_4930:
 mov_load sp, bp
serial_loc_4932:
 pop bp
serial_loc_4933:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=4
; REA ev_bd79a3c052ba08627d327ea92cb781d0d737a864823aa1c9d7d6ef1278ee991b
aspect_serial_timeout_operand:
serial_loc_e9f5:
 call aspect_string_option_flag
serial_loc_e9f8:
 or_load ax, ax
serial_loc_e9fa:
 jnz serial_loc_ea00
serial_loc_e9fc:
 mov ax, 0x1e
serial_loc_e9ff:
 ret
serial_loc_ea00:
 call aspect_dispatch_read
serial_loc_ea03:
 mov [aspect_operand_lookahead], ax
serial_loc_ea06:
 cmp ax, strict word 0x1a
serial_loc_ea09:
 jnz serial_loc_ea11
serial_loc_ea0b:
 sub_load ax, ax
serial_loc_ea0d:
 mov [aspect_operand_lookahead], ax
serial_loc_ea10:
 ret
serial_loc_ea11:
 mov ax, 0x1
serial_loc_ea14:
 push ax
serial_loc_ea15:
 mov ax, 0x7fff
serial_loc_ea18:
 push ax
serial_loc_ea19:
 call aspect_string_bounded_integer
serial_loc_ea1c:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=5
; REA ev_bb34d80c3c2dcaefa1cdb73320534cebc17d391b3e4dfc5cf08c1678563dd14a
aspect_serial_upper_byte:
serial_loc_8252:
 push bp
serial_loc_8253:
 mov_load bp, sp
serial_loc_8255:
 mov bx, word [bp + 0x4]
serial_loc_8258:
 test byte [bx + aspect_serial_ctype], 0x2
serial_loc_825d:
 jz serial_loc_8264
serial_loc_825f:
 lea ax, [bx + -0x20]
serial_loc_8262:
 jmp serial_loc_8266
serial_loc_8264:
 mov_load ax, bx
serial_loc_8266:
 pop bp
serial_loc_8267:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=6
; REA ev_2eaf19ee9ba800c0e82d059d807ffb959416900a1031497f312afe8165793857
aspect_serial_native_clock:
serial_loc_77fe:
 xor_load ax, ax
serial_loc_7800:
 mov es, ax
serial_loc_7802:
 cli
serial_loc_7803:
 mov ax, es:[0x46c]
serial_loc_7807:
 mov dx, word es:[0x46e]
serial_loc_780c:
 sti
serial_loc_780d:
 ret
%endif
%if ASPECT_SERIAL_COMMANDS_UNIT=0 || ASPECT_SERIAL_COMMANDS_UNIT=7
; REA ev_c92014699bbfb5dbf8fed01d6287ea0e103c217bbe7dcd9726c1f97bf8778691
aspect_serial_wait_status:
serial_loc_da32:
 mov ax,[aspect_serial_wait_result]
serial_loc_da35:
 ret
%endif
