; Maintained services for the recovered VT52 parser (reconstruction/vt52).
; Built only with --vt52 (TERMINAL_VT52); see docs/VT52.md. No DGROUP data.
;
; Near _TEXT is nearly full in every parent, so the parser, the ESC Y
; cursor address and these services live in the far VT52_CODE segment.
; _TEXT keeps only two entry stubs and two trampolines (19 bytes).
BITS 16
CPU 8086
%include "terminal_profile.inc"
extern csi_reset_terminal,csi_terminal_id,csi_previous_terminal_id
extern terminal_dec_keys,attributes_monochrome,screen_doublewidth_enabled
extern terminal_keymap,terminal_keymap_end
extern terminal_screen_print,terminal_controller_run,modes_value_3982
extern csi_transmit_byte,ansi_next_byte,screen_set_cursor
extern screen_cursor_up,screen_cursor_down,screen_cursor_right,screen_cursor_left
extern csi_service_da84,csi_service_d8b6,csi_service_da12
extern vt52_escape_entry

SEGMENT _TEXT public class=CODE use16
global terminal_escape_b98b,terminal_profile_switch_reset
; Escape dispatch entry for terminal id 1 (native b98b overlay thunk).
terminal_escape_b98b:
 call far vt52_escape_far
 ret
; Native 20a4 for runtime profile switches from the ANSI parser: DECANM
; (modes/core.asm) and the SCO id-2 switch (ansi/dispatch.asm).
terminal_profile_switch_reset:
 call far vt52_profile_reset_far
 ret
; BX = near service. The _arg form passes AX as the word a ret-2 callee pops.
vt52_near_call:
 call bx
 retf
vt52_near_call_arg:
 push ax
 call bx
 retf

SEGMENT VT52_CODE public align=16 class=FARCODE use16
global vt52f_next_byte,vt52f_profile_reset,vt52f_cursor_up,vt52f_cursor_down
global vt52f_cursor_right,vt52f_cursor_left,vt52f_set_cursor
global vt52f_reverse_index,vt52f_erase_after,vt52f_clear_screen
global vt52_print_row,vt52_print_screen,vt52_print_controller,vt52_identify
vt52_escape_far:
 call vt52_escape_entry
 retf
vt52_profile_reset_far:
 call vt52f_profile_reset
 retf

; Near services for the recovered code. BX is never a service input here.
vt52f_next_byte:
 mov bx,ansi_next_byte
 jmp short vt52_near
vt52f_cursor_up:
 mov bx,screen_cursor_up
 jmp short vt52_near
vt52f_cursor_down:
 mov bx,screen_cursor_down
 jmp short vt52_near
vt52f_cursor_right:
 mov bx,screen_cursor_right
 jmp short vt52_near
vt52f_cursor_left:
 mov bx,screen_cursor_left
 jmp short vt52_near
vt52f_set_cursor: ; AX row, DX column
 mov bx,screen_set_cursor
 jmp short vt52_near
vt52f_reverse_index:
 mov bx,csi_service_da84
 jmp short vt52_near
vt52f_clear_screen:
 mov bx,csi_service_da12
 jmp short vt52_near
; Native e3ca: full screen, or scroll region when modes_value_3982 is set,
; the same selection csi_media_copy makes for CSI i.
vt52_print_screen:
 mov ax,1
 cmp word [modes_value_3982],0
 je .print
 inc ax
.print:
 mov bx,terminal_screen_print
 jmp short vt52_near
; Native e2f8(selection), cdecl: ESC V passes 3 (cursor row).
vt52_print_row:
 mov bx,sp
 mov ax,[ss:bx+2]
 mov bx,terminal_screen_print
 jmp short vt52_near
; Native d0d0: printer controller; it ends on ESC X for profile 1.
vt52_print_controller:
 mov bx,terminal_controller_run
vt52_near:
 call far vt52_near_call
 ret

; Native d8b6(mode), callee pops: erase to end of screen (1) or line (0).
vt52f_erase_after:
 pop cx
 pop ax
 push cx
 mov bx,csi_service_d8b6
 call far vt52_near_call_arg
 ret

; Native abac(0x755e), callee pops: DS 755e is ESC / Z (VT52 identify).
; No DGROUP room for the string, so send its three bytes directly.
vt52_identify:
 mov ax,27
 call vt52_transmit
 mov ax,'/'
 call vt52_transmit
 mov ax,'Z'
 call vt52_transmit
 ret 2
vt52_transmit:
 mov bx,csi_transmit_byte
 call far vt52_near_call_arg
 ret

; Native 20a4(1) for a runtime profile switch (DECANM ESC[?2l, ESC <, and the
; SCO id-2 switch). The maintained RIS restores the configured snapshot,
; including the terminal id, so keep the id the caller selected and rebuild
; the per-id flags exactly as native reset.asm L_20c0..L_2114 does:
; doublewidth 1..11, DEC keys 2..11, monochrome 6..7. An id that is not
; runnable here (0, 12+) keeps the configured snapshot instead. The cdecl
; argument is ignored (caller cleans); all registers but AX are preserved.
vt52f_profile_reset:
 push bx
 push cx
 push dx
 push word [csi_previous_terminal_id]
 push word [csi_terminal_id]
 mov bx,csi_reset_terminal
 call far vt52_near_call
 pop ax
 pop dx
 active_profile_gate ax,.configured
 mov [csi_terminal_id],ax
 mov [csi_previous_terminal_id],dx
 xor dx,dx
 cmp ax,2
 jb .keys
 inc dx
.keys:
 mov [terminal_dec_keys],dx
 xor dx,dx
 cmp ax,6
 jb .mono
 cmp ax,7
 ja .mono
 inc dx
.mono:
 mov [attributes_monochrome],dx
 mov word [screen_doublewidth_enabled],1
 cmp ax,1
 jne .configured
 call vt52_cursor_keys
.configured:
 pop dx
 pop cx
 pop bx
 ret

; The snapshot keymap holds the configured ANSI cursor/PF strings. In VT52
; mode the terminal sends ESC A..D and ESC P..S instead (DEC VT52 key codes);
; rewrite only exact ESC [ x / ESC O x entries. Leaving VT52 restores the
; snapshot keymap through csi_reset_terminal.
vt52_cursor_keys:
 mov bx,terminal_keymap
.entry:
 cmp byte [bx],27
 jne .next
 mov al,[bx+1]
 cmp al,'['
 je .final
 cmp al,'O'
 jne .next
.final:
 cmp byte [bx+3],0
 jne .next
 mov al,[bx+2]
 cmp al,'A'
 jb .next
 cmp al,'D'
 jbe .rewrite
 cmp al,'P'
 jb .next
 cmp al,'S'
 ja .next
.rewrite:
 mov [bx+1],al
 mov byte [bx+2],0
.next:
 add bx,12
 cmp bx,terminal_keymap_end
 jb .entry
 ret
