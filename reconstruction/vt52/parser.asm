; Recovered PCPlus 2.01 VT52 escape parser (overlay 14, f02e..f12c); see docs/VT52.md.
; The flat build is checked against the original by recover.py (analyst only).
BITS 16
CPU 8086
%ifdef VT52_OMF
; Far bank (src/terminal/vt52_live.asm): native near services are reached
; through VT52_CODE-local stubs, so each recovered name maps to its stub.
SEGMENT VT52_CODE public align=16 class=FARCODE use16
global vt52_escape_entry
extern vt52f_next_byte,vt52f_profile_reset,vt52f_cursor_up,vt52f_cursor_down
extern vt52f_cursor_right,vt52f_cursor_left,vt52f_set_cursor
extern vt52f_reverse_index,vt52f_erase_after,vt52f_clear_screen
extern vt52_print_row,vt52_print_controller,vt52_print_screen,vt52_identify
extern vt52_cursor_address
extern csi_terminal_id,csi_previous_terminal_id,csi_wrap_pending
extern ansi_charset_g0_flag_graphics
%define ansi_next_byte vt52f_next_byte
%define vt52_profile_reset vt52f_profile_reset
%define screen_cursor_up vt52f_cursor_up
%define screen_cursor_down vt52f_cursor_down
%define screen_cursor_right vt52f_cursor_right
%define screen_cursor_left vt52f_cursor_left
%define screen_set_cursor vt52f_set_cursor
%define csi_service_da84 vt52f_reverse_index
%define csi_service_d8b6 vt52f_erase_after
%define csi_service_da12 vt52f_clear_screen
; The maintained identify stub writes ESC / Z itself; the native DS string
; address is a dead argument there.
%define vt52_identify_string 0
%define short
%else
ORG 0xf02e
%define ansi_next_byte 0x5ca0
%define vt52_profile_reset 0x20a4
%define screen_cursor_up 0x1efc
%define screen_cursor_down 0x1e0c
%define screen_cursor_right 0x1ea0
%define screen_cursor_left 0x1e30
%define screen_set_cursor 0x1bbe
%define csi_service_da84 0xda84
%define csi_service_d8b6 0xd8b6
%define csi_service_da12 0xda12
%define vt52_print_row 0xe2f8
%define vt52_print_controller 0xd0d0
%define vt52_print_screen 0xe3ca
%define vt52_identify 0xabac
%define vt52_cursor_address 0x1f70
%define csi_terminal_id 0x1d18
%define csi_previous_terminal_id 0x321e
%define csi_wrap_pending 0x3342
%define ansi_charset_g0_flag_graphics 0xcdec
%define vt52_identify_string 0x755e
%endif
%include "encodings.inc"
%ifndef VT52_OMF
terminal_escape_b98b:
%endif
vt52_escape_entry:
L_f02e: push si
L_f02f: call ansi_next_byte
L_f032: mov_load si,ax
L_f034: or_load si,si
L_f036: jz short L_f02f
L_f038: sub ax,strict word 0x3c
L_f03b: cmp ax,strict word 0x21
L_f03e: jna short L_f043
L_f040: jmp near L_f129
L_f043: shl ax,1
L_f045: xchg ax,bx
L_f046: jmp word near [cs:bx+vt52_command_table]
L_f04b: nop
vt52_command_table:
 dw L_f090 ; <  leave VT52 (previous profile, reset)
 dw L_f129 ; =  keypad modes ignored
 dw L_f129 ; >
 dw L_f129 ; ?
 dw L_f129 ; @
 dw L_f0a4 ; A  cursor up
 dw L_f0b0 ; B  cursor down
 dw L_f0b6 ; C  cursor right
 dw L_f0bc ; D  cursor left
 dw L_f129 ; E
 dw L_f0c2 ; F  graphics on
 dw L_f0ca ; G  graphics off
 dw L_f0d2 ; H  home
 dw L_f0da ; I  reverse index
 dw L_f0e0 ; J  erase to end of screen
 dw L_f0f0 ; K  erase to end of line
 dw L_f0fa ; L  (PCPlus) clear screen
 dw L_f129 ; M
 dw L_f129 ; N
 dw L_f129 ; O
 dw L_f129 ; P
 dw L_f129 ; Q
 dw L_f129 ; R
 dw L_f129 ; S
 dw L_f129 ; T
 dw L_f129 ; U
 dw L_f100 ; V  print cursor line
 dw L_f10a ; W  printer controller on
 dw L_f129 ; X
 dw L_f110 ; Y  direct cursor address
 dw L_f11c ; Z  identify
 dw L_f129 ; [
 dw L_f129 ; backslash
 dw L_f126 ; ]  print screen
L_f090: mov ax,[csi_previous_terminal_id]
L_f093: mov [csi_terminal_id],ax
L_f096: mov ax,0x1
L_f099: push ax
L_f09a: call vt52_profile_reset
L_f09d: add sp,strict byte 0x2
L_f0a0: jmp near L_f129
L_f0a3: nop
L_f0a4: call screen_cursor_up
L_f0a7: mov word [csi_wrap_pending],0x0
L_f0ad: jmp short L_f129
L_f0af: nop
L_f0b0: call screen_cursor_down
L_f0b3: jmp short L_f0a7
L_f0b5: nop
L_f0b6: call screen_cursor_right
L_f0b9: jmp short L_f0a7
L_f0bb: nop
L_f0bc: call screen_cursor_left
L_f0bf: jmp short L_f129
L_f0c1: nop
L_f0c2: mov word [ansi_charset_g0_flag_graphics],0x1
L_f0c8: jmp short L_f129
L_f0ca: mov word [ansi_charset_g0_flag_graphics],0x0
L_f0d0: jmp short L_f129
L_f0d2: sub_load ax,ax
L_f0d4: cwd
L_f0d5: call screen_set_cursor
L_f0d8: jmp short L_f129
L_f0da: call csi_service_da84
L_f0dd: jmp short L_f129
L_f0df: nop
L_f0e0: mov word [csi_wrap_pending],0x0
L_f0e6: mov ax,0x1
L_f0e9: push ax
L_f0ea: call csi_service_d8b6
L_f0ed: pop si
L_f0ee: ret
L_f0ef: nop
L_f0f0: mov word [csi_wrap_pending],0x0
L_f0f6: sub_load ax,ax
L_f0f8: jmp short L_f0e9
L_f0fa: call csi_service_da12
L_f0fd: pop si
L_f0fe: ret
L_f0ff: nop
L_f100: mov ax,0x3
L_f103: push ax
L_f104: call vt52_print_row
L_f107: jmp short L_f09d
L_f109: nop
L_f10a: call vt52_print_controller
L_f10d: pop si
L_f10e: ret
L_f10f: nop
L_f110: mov word [csi_wrap_pending],0x0
L_f116: call vt52_cursor_address
L_f119: pop si
L_f11a: ret
L_f11b: nop
L_f11c: mov ax,vt52_identify_string
L_f11f: push ax
L_f120: call vt52_identify
L_f123: pop si
L_f124: ret
L_f125: nop
L_f126: call vt52_print_screen
L_f129: pop si
L_f12a: ret
L_f12b: nop
