; Exact PCPlus2.01 native ASPECT COMGETC/COMGETCD/RGET/WAITQUIET.
; OriginalSHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS,DF=0, nearRET, BP/SI/DI preserved; otherregs/flags volatile.
; read_integer/read_control RET2, character(echo,delayed) RET4, serial_receive
; RET2, native_time RET2; other scalar services RET. Full4C74 character
; translation/pattern-monitor/renderer behavior remains an explicit device boundary.
; RGET status0=CR/full/cancel,1=timeout; CR is replaced by terminator.
; Native zero-length pointer check is retained: zero length may still consume
; and store bytes untilCR/cancel/timeout. This is not a safe bounded reader.
; RGET counts observed DOS-second changes, not elapsed-time differences.
; WAITQUIET drains all available bytes perwait then resets quiet counter;
; cancellation is only checked outside drain. Status0=quiet,1=incomplete.
; Native delayed read waits36BIOSlowword clock transitions, enablesIF, ES=0.
; Native DOS time struct: hundredths,hour,minute,second words. FOREVER22=1.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_RECEIVE_COMMANDS_FLAT
%if ASPECT_RECEIVE_COMMANDS_UNIT=1
ORG 0x5431
%elif ASPECT_RECEIVE_COMMANDS_UNIT=2
ORG 0x50c7
%elif ASPECT_RECEIVE_COMMANDS_UNIT=3
ORG 0x52d0
%elif ASPECT_RECEIVE_COMMANDS_UNIT=4
ORG 0x4c4f
%elif ASPECT_RECEIVE_COMMANDS_UNIT=5
ORG 0x3323
%elif ASPECT_RECEIVE_COMMANDS_UNIT=6
ORG 0x778c
%elif ASPECT_RECEIVE_COMMANDS_UNIT=7
ORG 0x5ca0
%elif ASPECT_RECEIVE_COMMANDS_UNIT=8
ORG 0xda08
%elif ASPECT_RECEIVE_COMMANDS_UNIT=9
ORG 0xda10
%else
%error Select ASPECT_RECEIVE_COMMANDS_UNIT1..9
%endif
%define aspect_expr_integer_address 0xce13
%define aspect_string_read_destination 0xce2b
%define aspect_string_option_flag 0xcd5f
%define aspect_string_length_operand 0xcde3
%define aspect_console_pause_operand 0xcdd7
%define aspect_string_flush 0xcd47
%define aspect_serial_timeout_operand 0xcd83
%define aspect_receive_seconds 0x3323
%define aspect_console_cancel_poll 0x4e34
%define aspect_serial_receive 0x4c3c
%define aspect_console_wait_second 0x6bb6
%define aspect_receive_character 0x4c74
%define aspect_receive_raw_read 0xaa65
%define aspect_serial_rx_count 0x8e20
%define aspect_string_compare_result 0xd124
%define aspect_receive_display 0xe37e
%define aspect_receive_suppress_echo 0xe382
%define aspect_receive_clock_sample 0x8f02
%if ASPECT_RECEIVE_COMMANDS_UNIT!=1
%define aspect_receive_comgetc 0x5431
%define aspect_receive_comgetcd 0x5438
%define aspect_receive_read_integer 0x5440
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=2
%define aspect_receive_rget 0x50c7
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=3
%define aspect_receive_wait_quiet 0x52d0
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=4
%define aspect_receive_read_control 0x4c4f
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=5
%define aspect_receive_native_seconds 0x3323
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=6
%define aspect_receive_native_time 0x778c
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=7
%define aspect_receive_native_delayed_read 0x5ca0
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=8
%define aspect_receive_available_status 0xda08
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT!=9
%define aspect_receive_forever 0xda10
%endif
%else
%define ASPECT_RECEIVE_COMMANDS_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_receive_comgetc
global aspect_receive_comgetcd
global aspect_receive_read_integer
global aspect_receive_rget
global aspect_receive_wait_quiet
global aspect_receive_read_control
global aspect_receive_native_seconds
global aspect_receive_native_time
global aspect_receive_native_delayed_read
global aspect_receive_available_status
global aspect_receive_forever
extern aspect_expr_integer_address
extern aspect_string_read_destination
extern aspect_string_option_flag
extern aspect_string_length_operand
extern aspect_console_pause_operand
extern aspect_string_flush
extern aspect_serial_timeout_operand
extern aspect_receive_seconds
extern aspect_console_cancel_poll
extern aspect_serial_receive
extern aspect_console_wait_second
extern aspect_receive_character
extern aspect_receive_raw_read
extern aspect_serial_rx_count
extern aspect_string_compare_result
extern aspect_receive_display
extern aspect_receive_suppress_echo
extern aspect_receive_clock_sample
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=1
; REA ev_c9dab30cc645eee5ec43b9c257351cb06ed04905c99caac895e68955da512b49
aspect_receive_comgetc:
receive_loc_5431:
 sub_load ax, ax
receive_loc_5433:
 push ax
receive_loc_5434:
 call aspect_receive_read_integer
receive_loc_5437:
 ret
; REA ev_13343466be9407aa7480f3e19504a11d087fb562037b23d2350507dea98a4308
aspect_receive_comgetcd:
receive_loc_5438:
 mov ax, 0x1
receive_loc_543b:
 push ax
receive_loc_543c:
 call aspect_receive_read_integer
receive_loc_543f:
 ret
; REA ev_9b26294f6326bfe19c6a7339480be9e12cf43c4875bf6e0195d932450446af0a
aspect_receive_read_integer:
receive_loc_5440:
 push bp
receive_loc_5441:
 mov_load bp, sp
receive_loc_5443:
 push si
receive_loc_5444:
 call aspect_expr_integer_address
receive_loc_5447:
 mov_load si, ax
receive_loc_5449:
 push word [bp + 0x4]
receive_loc_544c:
 call aspect_receive_read_control
receive_loc_544f:
 mov word [si], ax
receive_loc_5451:
 pop si
receive_loc_5452:
 mov_load sp, bp
receive_loc_5454:
 pop bp
receive_loc_5455:
 ret 0x2
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=2
; REA ev_ff44e1f3a6b278c97178ac1293a6dc35f34e4a73181fdcf21fa5ae9ccd9113ab
aspect_receive_rget:
receive_loc_50c7:
 push bp
receive_loc_50c8:
 mov_load bp, sp
receive_loc_50ca:
 sub sp, 0x4
receive_loc_50cd:
 push di
receive_loc_50ce:
 push si
receive_loc_50cf:
 call aspect_string_read_destination
receive_loc_50d2:
 mov_load si, ax
receive_loc_50d4:
 call aspect_string_option_flag
receive_loc_50d7:
 mov_load di, ax
receive_loc_50d9:
 or_load di, di
receive_loc_50db:
 jz receive_loc_50e2
receive_loc_50dd:
 call aspect_string_length_operand
receive_loc_50e0:
 jmp receive_loc_50e5
receive_loc_50e2:
 mov ax, 0x50
receive_loc_50e5:
 add_load ax, si
receive_loc_50e7:
 mov word [bp + -0x2], ax
receive_loc_50ea:
 or_load di, di
receive_loc_50ec:
 jz receive_loc_50fc
receive_loc_50ee:
 call aspect_string_option_flag
receive_loc_50f1:
 or_load ax, ax
receive_loc_50f3:
 jz receive_loc_50fc
receive_loc_50f5:
 call aspect_console_pause_operand
receive_loc_50f8:
 mov_load di, ax
receive_loc_50fa:
 jmp receive_loc_50ff
receive_loc_50fc:
 mov di, 0x1e
receive_loc_50ff:
 call aspect_receive_seconds
receive_loc_5102:
 mov word [bp + -0x4], ax
receive_loc_5105:
 mov word [aspect_string_compare_result], 0x1
receive_loc_510b:
 jmp receive_loc_513f
receive_loc_510d:
 cmp word [bp + -0x2], 0x0
receive_loc_5111:
 jz receive_loc_5143
receive_loc_5113:
 call aspect_console_cancel_poll
receive_loc_5116:
 or_load ax, ax
receive_loc_5118:
 jnz receive_loc_5143
receive_loc_511a:
 cmp word [aspect_serial_rx_count], ax
receive_loc_511e:
 jz receive_loc_5130
receive_loc_5120:
 push ax
receive_loc_5121:
 call aspect_serial_receive
receive_loc_5124:
 mov byte [si], al
receive_loc_5126:
 cmp al, 0xd
receive_loc_5128:
 jz receive_loc_5143
receive_loc_512a:
 inc si
receive_loc_512b:
 cmp si, word [bp + -0x2]
receive_loc_512e:
 jz receive_loc_5143
receive_loc_5130:
 call aspect_receive_seconds
receive_loc_5133:
 cmp ax, word [bp + -0x4]
receive_loc_5136:
 jz receive_loc_513f
receive_loc_5138:
 call aspect_receive_seconds
receive_loc_513b:
 mov word [bp + -0x4], ax
receive_loc_513e:
 dec di
receive_loc_513f:
 or_load di, di
receive_loc_5141:
 jnz receive_loc_510d
receive_loc_5143:
 mov byte [si], 0x0
receive_loc_5146:
 or_load di, di
receive_loc_5148:
 jz receive_loc_514e
receive_loc_514a:
 dec word [aspect_string_compare_result]
receive_loc_514e:
 call aspect_string_flush
receive_loc_5151:
 pop si
receive_loc_5152:
 pop di
receive_loc_5153:
 mov_load sp, bp
receive_loc_5155:
 pop bp
receive_loc_5156:
 ret
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=3
; REA ev_1acfbe007021c1d8d9a5ed773850e95dcd287242ab3aa51f2e810ce3d75b89ca
aspect_receive_wait_quiet:
receive_loc_52d0:
 push bp
receive_loc_52d1:
 mov_load bp, sp
receive_loc_52d3:
 sub sp, 0x6
receive_loc_52d6:
 push di
receive_loc_52d7:
 push si
receive_loc_52d8:
 call aspect_string_option_flag
receive_loc_52db:
 or_load ax, ax
receive_loc_52dd:
 jz receive_loc_52ec
receive_loc_52df:
 call aspect_console_pause_operand
receive_loc_52e2:
 mov word [bp + -0x4], ax
receive_loc_52e5:
 call aspect_serial_timeout_operand
receive_loc_52e8:
 mov_load di, ax
receive_loc_52ea:
 jmp receive_loc_52f4
receive_loc_52ec:
 mov word [bp + -0x4], 0xf
receive_loc_52f1:
 mov di, 0x1e
receive_loc_52f4:
 mov si, word [bp + -0x4]
receive_loc_52f7:
 mov word [bp + -0x2], di
receive_loc_52fa:
 mov word [bp + -0x6], di
receive_loc_52fd:
 jmp receive_loc_5332
receive_loc_52ff:
 cmp word [bp + -0x2], 0x0
receive_loc_5303:
 jnz receive_loc_530b
receive_loc_5305:
 cmp word [bp + -0x6], 0x0
receive_loc_5309:
 jnz receive_loc_5336
receive_loc_530b:
 call aspect_console_cancel_poll
receive_loc_530e:
 or_load ax, ax
receive_loc_5310:
 jnz receive_loc_5336
receive_loc_5312:
 call aspect_console_wait_second
receive_loc_5315:
 cmp word [aspect_serial_rx_count], 0x0
receive_loc_531a:
 jnz receive_loc_531f
receive_loc_531c:
 dec si
receive_loc_531d:
 jmp receive_loc_532f
receive_loc_531f:
 sub_load ax, ax
receive_loc_5321:
 push ax
receive_loc_5322:
 call aspect_serial_receive
receive_loc_5325:
 cmp word [aspect_serial_rx_count], 0x0
receive_loc_532a:
 jnz receive_loc_531f
receive_loc_532c:
 mov si, word [bp + -0x4]
receive_loc_532f:
 dec word [bp + -0x2]
receive_loc_5332:
 or_load si, si
receive_loc_5334:
 jnz receive_loc_52ff
receive_loc_5336:
 cmp si, 0x1
receive_loc_5339:
 sbb_load ax, ax
receive_loc_533b:
 inc ax
receive_loc_533c:
 mov [aspect_string_compare_result], ax
receive_loc_533f:
 pop si
receive_loc_5340:
 pop di
receive_loc_5341:
 mov_load sp, bp
receive_loc_5343:
 pop bp
receive_loc_5344:
 ret
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=4
; REA ev_325a48caba3fd354c5614a573cab7c38e0677459060fd24ca4780021f0150abd
aspect_receive_read_control:
receive_loc_4c4f:
 push bp
receive_loc_4c50:
 mov_load bp, sp
receive_loc_4c52:
 cmp word [aspect_receive_display], 0x0
receive_loc_4c57:
 jz receive_loc_4c65
receive_loc_4c59:
 cmp word [aspect_receive_suppress_echo], 0x0
receive_loc_4c5e:
 jnz receive_loc_4c65
receive_loc_4c60:
 mov dx, 0x1
receive_loc_4c63:
 jmp receive_loc_4c67
receive_loc_4c65:
 sub_load dx, dx
receive_loc_4c67:
 push word [bp + 0x4]
receive_loc_4c6a:
 push dx
receive_loc_4c6b:
 call aspect_receive_character
receive_loc_4c6e:
 mov_load sp, bp
receive_loc_4c70:
 pop bp
receive_loc_4c71:
 ret 0x2
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=5
; REA ev_934cab24472592ef1451e2de57a9498b07325d9fd754388190419504484a4e95
aspect_receive_native_seconds:
receive_loc_3323:
 mov ax, aspect_receive_clock_sample
receive_loc_3326:
 push ax
receive_loc_3327:
 call aspect_receive_native_time
receive_loc_332a:
 mov ax, [aspect_receive_clock_sample+6]
receive_loc_332d:
 ret
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=6
; REA ev_5836cefcd82001ced9051bae7c7c0b4fb945d6640bd348c4996e22a04fd49c05
aspect_receive_native_time:
receive_loc_778c:
 mov_load bx, sp
receive_loc_778e:
 mov bx, word [bx + 0x2]
receive_loc_7791:
 mov ah, 0x2c
receive_loc_7793:
 int 0x21
receive_loc_7795:
 sub_load ah, ah
receive_loc_7797:
 mov_load al, dl
receive_loc_7799:
 mov word [bx], ax
receive_loc_779b:
 mov_load al, ch
receive_loc_779d:
 mov word [bx + 0x2], ax
receive_loc_77a0:
 mov_load al, cl
receive_loc_77a2:
 mov word [bx + 0x4], ax
receive_loc_77a5:
 mov_load al, dh
receive_loc_77a7:
 mov word [bx + 0x6], ax
receive_loc_77aa:
 ret 0x2
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=7
; REA ev_75901cf30111f91f6e0d7beb16b3be24cf1dada409883b761d14c7cd9319112c
aspect_receive_native_delayed_read:
receive_loc_5ca0:
 cmp word [aspect_serial_rx_count], 0x0
receive_loc_5ca5:
 jnz receive_loc_5cca
receive_loc_5ca7:
 mov dx, 0x24
receive_loc_5caa:
 sti
receive_loc_5cab:
 xor_load cx, cx
receive_loc_5cad:
 mov es, cx
receive_loc_5caf:
 mov bx, 0x46c
receive_loc_5cb2:
 mov ax, word es:[bx]
receive_loc_5cb5:
 cmp word [aspect_serial_rx_count], 0x0
receive_loc_5cba:
 jnz receive_loc_5cca
receive_loc_5cbc:
 cmp ax, word es:[bx]
receive_loc_5cbf:
 jz receive_loc_5cb5
receive_loc_5cc1:
 inc cx
receive_loc_5cc2:
 cmp_load cx, dx
receive_loc_5cc4:
 jc receive_loc_5cb2
receive_loc_5cc6:
 mov ax, 0xffff
receive_loc_5cc9:
 ret
receive_loc_5cca:
 call aspect_receive_raw_read
receive_loc_5ccd:
 ret
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=8
; REA ev_cdae2f605047d9c96059bd934fd65f90c1b0d4563bb256ff2b4884088b53feb7
aspect_receive_available_status:
receive_loc_da08:
 mov ax, [aspect_serial_rx_count]
receive_loc_da0b:
 ret
%endif
%if ASPECT_RECEIVE_COMMANDS_UNIT=0 || ASPECT_RECEIVE_COMMANDS_UNIT=9
; REA ev_2d53680647f14e4a928eda45e66f7ede35264bf7ba3bb77bf375277ade3f0162
aspect_receive_forever:
receive_loc_da10:
 mov ax, 0x1
receive_loc_da13:
 ret
%endif
