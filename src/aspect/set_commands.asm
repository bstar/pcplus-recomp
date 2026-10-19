; Recovered PCPlus2.01 selected SET handlers, bounded numeric readers and GET helpers.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS; near calls. boolean/decimal readers RET2; other exports RET.
; Dispatcher table, status refresh and GET destination remain external services.
; Native boolean writes raw bytes; RXDATA aliases the actual flow gate.
; PAUSECHAR stores a byte and GET sign-extends it; do not replace with a word store.
; REA generic E6BB ev_0eac28aff291b49ec3d0558f8f05ee1eedb3010924224c14dc0014c056185ef8.
; REA decimal DDA7 ev_c83f8fc5153ef8704ecf7828b52bc9309a198836822c9abf045419b163d1a79b.
; Tiny wrappers/dispatcher additionally bound by original ranges/hashes and replay.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SET_FLAT
%if ASPECT_SET_UNIT=1
ORG 0x5458
%endif
%if ASPECT_SET_UNIT=2
ORG 0xe6bb
%endif
%if ASPECT_SET_UNIT=3
ORG 0xe953
%endif
%if ASPECT_SET_UNIT=4
ORG 0xe993
%endif
%if ASPECT_SET_UNIT=5
ORG 0xea1c
%endif
%if ASPECT_SET_UNIT=6
ORG 0xea49
%endif
%if ASPECT_SET_UNIT=7
ORG 0xea6d
%endif
%if ASPECT_SET_UNIT=8
ORG 0xebb4
%endif
%if ASPECT_SET_UNIT=9
ORG 0xec77
%endif
%if ASPECT_SET_UNIT=10
ORG 0xee37
%endif
%if ASPECT_SET_UNIT=11
ORG 0xeaad
%endif
%if ASPECT_SET_UNIT=12
ORG 0xed76
%endif
%if ASPECT_SET_UNIT=13
ORG 0xdda7
%endif
%if ASPECT_SET_UNIT=14
ORG 0xddf9
%endif
%define aspect_set_query_mode 0xe38e
%define aspect_dispatch_read 0x4cb4
%define aspect_set_table 0x4d24
%define aspect_set_status_refresh 0x2fb8
%define aspect_set_query_integer 0xde3a
%define aspect_receive_display 0xe37e
%define aspect_serial_local_echo 0x1d1a
%define aspect_set_findcase_value 0xe392
%define aspect_when_keyboard_disabled 0xe380
%define aspect_console_message_mode 0xe38a
%define aspect_flow_wait_gate 0xe382
%define aspect_set_switchcase_value 0xe394
%define aspect_serial_case_sensitive 0xe396
%define aspect_when_case_sensitive 0xe398
%define aspect_serial_pause_character 0x1d66
%define aspect_serial_character_delay_value 0x1d68
%define aspect_string_bounded_integer 0xdd68
%if ASPECT_SET_UNIT!=2
%define aspect_set_boolean 0xe6bb
%endif
%if ASPECT_SET_UNIT!=14
%define aspect_set_printable_integer 0xddf9
%endif
%if ASPECT_SET_UNIT!=13
%define aspect_set_decimal_integer 0xdda7
%endif
%else
%define ASPECT_SET_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_set_dispatch
global aspect_set_boolean
global aspect_set_display
global aspect_set_duplex
global aspect_set_findcase
global aspect_set_keys
global aspect_set_msg_crlf
global aspect_set_rxdata
global aspect_set_switchcase
global aspect_set_waitcase
global aspect_set_pausechar
global aspect_set_txpace
global aspect_set_decimal_integer
global aspect_set_printable_integer
global aspect_set_whencase
extern aspect_set_query_mode
extern aspect_dispatch_read
extern aspect_set_table
extern aspect_set_status_refresh
extern aspect_set_query_integer
extern aspect_receive_display
extern aspect_serial_local_echo
extern aspect_set_findcase_value
extern aspect_when_keyboard_disabled
extern aspect_console_message_mode
extern aspect_flow_wait_gate
extern aspect_set_switchcase_value
extern aspect_serial_case_sensitive
extern aspect_when_case_sensitive
extern aspect_serial_pause_character
extern aspect_serial_character_delay_value
extern aspect_string_bounded_integer
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=1
aspect_set_dispatch:
 mov word [aspect_set_query_mode],0
 call aspect_dispatch_read
 mov_load bx,ax
 shl bx,1
 call word [bx+aspect_set_table]
 jmp near aspect_set_status_refresh
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=2
aspect_set_boolean:
 push bp
 mov_load bp,sp
 cmp word [aspect_set_query_mode],0
 jnz .get
 call aspect_dispatch_read
 mov bx,[bp+4]
 mov [bx],ax
 jmp short .done
.get:
 mov bx,[bp+4]
 push word [bx]
 call aspect_set_query_integer
.done:
 mov_load sp,bp
 pop bp
 ret 2
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=3
aspect_set_display:
 mov ax,aspect_receive_display
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=4
aspect_set_duplex:
 mov ax,aspect_serial_local_echo
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=5
aspect_set_findcase:
 mov ax,aspect_set_findcase_value
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=6
aspect_set_keys:
 mov ax,aspect_when_keyboard_disabled
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=7
aspect_set_msg_crlf:
 mov ax,aspect_console_message_mode
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=8
aspect_set_rxdata:
 mov ax,aspect_flow_wait_gate
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=9
aspect_set_switchcase:
 mov ax,aspect_set_switchcase_value
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=10
aspect_set_waitcase:
 mov ax,aspect_serial_case_sensitive
 push ax
 call aspect_set_boolean
 ret
aspect_set_whencase:
 mov ax,aspect_when_case_sensitive
 push ax
 call aspect_set_boolean
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=11
aspect_set_pausechar:
 cmp word [aspect_set_query_mode],0
 jnz .get
 call aspect_set_printable_integer
 mov [aspect_serial_pause_character],al
 ret
.get:
 mov al,[aspect_serial_pause_character]
 cbw
 push ax
 call aspect_set_query_integer
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=12
aspect_set_txpace:
 cmp word [aspect_set_query_mode],0
 jnz .get
 mov ax,3
 push ax
 call aspect_set_decimal_integer
 mov [aspect_serial_character_delay_value],ax
 ret
.get:
 push word [aspect_serial_character_delay_value]
 call aspect_set_query_integer
 ret
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=13
aspect_set_decimal_integer:
 push bp
 mov_load bp,sp
 push di
 mov di,10
 jmp short .next
.again:
 mov ax,10
 mul di
 mov_load di,ax
.next:
 dec word [bp+4]
 jnz .again
 sub_load ax,ax
 push ax
 lea ax,[di-1]
 push ax
 call aspect_string_bounded_integer
 pop di
 mov_load sp,bp
 pop bp
 ret 2
%endif
%if ASPECT_SET_UNIT=0 || ASPECT_SET_UNIT=14
aspect_set_printable_integer:
 mov ax,32
 push ax
 mov ax,126
 push ax
 call aspect_string_bounded_integer
 ret
%endif
