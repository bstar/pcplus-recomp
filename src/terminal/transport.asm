; Maintained live transport over the actual recovered UART and keyboard modules.
; Near calls, DS=SS. Public callbacks preserve BP/SI/DI (and ES).
; Single foreground producer/consumer TX ring; UART ISR owns RX only.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_receive_byte,uart_unreceive_byte,uart_try_write,uart_poll_flow
extern keyboard_poll,terminal_read_key
extern terminal_quit,terminal_exit_code
extern keyboard_classify_raw,terminal_enqueue_key_slot
extern terminal_ansi_wait_active,terminal_ansi_wait_cancel
extern _terminal_autostart_flush
extern terminal_connection_poll,terminal_connection_cancel,terminal_connection_start
extern terminal_connection_exit,connection_state,connection_enabled
extern terminal_macro_active,terminal_macro_start,terminal_macro_poll,terminal_macro_cancel
extern terminal_macro_tx_allowed,terminal_macro_tx_epoch,terminal_defer_key,terminal_take_deferred_key
extern terminal_program_pending,terminal_program_cancel
extern terminal_transfer_start
extern terminal_upload_start
extern terminal_capture_toggle,terminal_capture_pause,terminal_capture_crlf,terminal_capture_flush
extern terminal_snapshot_start
extern terminal_monitor_key
extern terminal_controller_key
extern terminal_break_start,terminal_break_poll,terminal_break_cancel
extern terminal_printer_toggle
extern terminal_setup_start
extern terminal_translation_reload_start
extern terminal_script_start
extern terminal_translation_edit_start
extern terminal_redisplay_key,terminal_clipboard_remaining
extern terminal_menu_pending,terminal_deferred_count,terminal_deferred_head,terminal_deferred_tail
extern terminal_parser_active,_redisplay_active,_command_menu_active
extern terminal_aspect_active,terminal_render_read,terminal_render_unread
extern terminal_render_poll,terminal_render_send,terminal_render_string
extern terminal_key_output
global terminal_menu_pending_poll
global terminal_poll_io,terminal_enqueue_al,terminal_enqueue_user_al,terminal_tick_low,terminal_clock_ticks
extern terminal_tx_origin_set_far,terminal_tx_origin_delivered_far
global ansi_next_byte,ansi_unread_byte,csi_transmit_byte,csi_transmit_string

; Read only the low BIOS tick word. Unsigned subtraction handles 16-bit wrap.
; BIOS midnight reset can end the wait early; it cannot extend this deadline.
terminal_tick_low:
 push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 pop es
 ret

; Atomic full BIOS day-tick snapshot, DX:AX. Preserve the caller's IF and ES.
terminal_clock_ticks:
 push es
 pushf
 cli
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 ret

; Consume one actual RX byte, including NUL, or return ffff after36 BIOS ticks.
; Continue servicing flow, bounded TX and keyboard/Alt-X while waiting.
ansi_next_byte:
 cmp word [terminal_aspect_active],0
 je .ordinary
 call far terminal_render_read
 ret
.ordinary:
 push bp
 push si
 push di
 push es
 call terminal_tick_low
 mov si,ax
.wait:
 cmp word [terminal_quit],0
 jne .timeout
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne .timeout
 cmp word [terminal_program_pending],0
 jne .timeout
 cmp word [connection_state],0
 je .receive
 cmp word [connection_state],6
 jne .timeout ; Yield a partial parser to modem control ownership.
.receive:
 call uart_receive_byte
 cmp ax,0xffff
 je .empty
 jmp .done
.empty:
 call terminal_tick_low
 sub ax,si
 cmp ax,36
 jb .wait
.timeout:
 mov ax,0xffff
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Original parser calls this only immediately after consuming a byte.
ansi_unread_byte:
 cmp word [terminal_aspect_active],0
 je .ordinary
 call far terminal_render_unread
 ret
.ordinary:
 jmp uart_unreceive_byte

; AL -> bounded TX queue. No busy wait, no local echo. AX is preserved.
; Overflow terminates the session with explicit error3 instead of losing bytes.
terminal_enqueue_al:
 push dx
 xor dx,dx
 jmp terminal_enqueue_classified
terminal_enqueue_user_al:
 push dx
 mov dx,1
terminal_enqueue_classified:
 cmp word [terminal_aspect_active],0
 je .ordinary
 push ax
 and ax,255
 call far terminal_render_send
 pop ax
 pop dx
 ret
.ordinary:
 push bx
 cmp word [terminal_quit],0
 jne .done
 cmp word [terminal_tx_count],1024
 jae .overflow
 mov bx,[terminal_tx_tail]
 mov [terminal_tx_buffer+bx],al
 call far terminal_tx_origin_set_far
 inc bx
 and bx,1023
 mov [terminal_tx_tail],bx
 inc word [terminal_tx_count]
.done:
 pop bx
 pop dx
 ret
.overflow:
 mov word [terminal_exit_code],3
 mov word [terminal_quit],1
 jmp .done

; Original report/output ABI: word argument, callee cleanup RET2.
csi_transmit_byte:
 cmp word [terminal_aspect_active],0
 je .ordinary
 mov bx,sp
 mov ax,[ss:bx+2]
 call far terminal_render_send
 ret 2
.ordinary:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,[bp+4]
 call terminal_enqueue_al
 pop es
 pop di
 pop si
 pop bp
 ret 2

csi_transmit_string:
 cmp word [terminal_aspect_active],0
 je .ordinary
 mov bx,sp
 mov ax,[ss:bx+2]
 call far terminal_render_string
 ret 2
.ordinary:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov si,[bp+4]
.next:
 cmp word [terminal_quit],0
 jne .done
 lodsb
 or al,al
 jz .done
 call terminal_enqueue_al
 jmp .next
.done:
 pop es
 pop di
 pop si
 pop bp
 ret 2

terminal_poll_io:
 cmp word [terminal_aspect_active],0
 je .ordinary
 call far terminal_render_poll
 ret
.ordinary:
 push bp
 push si
 push di
 push es
 call terminal_poll_serial
 cmp word [terminal_quit],0
%ifdef TERMINAL_KEYBOARD_BANK
 jne terminal_poll_io_return
%else
 jne .done
%endif
 ; Keep request service distinct from every possible BIOS key, including AX0.
 call terminal_menu_pending_poll
%ifdef TERMINAL_KEYBOARD_BANK
 ; Retained dispatcher bank, not an overlay or a second keyboard owner. Keep
 ; the original saved-register frame here; the bank releases only its own
 ; far return. All near services below use register/no-argument contracts.
 call far terminal_keyboard_dispatch_far
terminal_poll_io_return:
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT KEYBOARD_CODE public align=16 class=FARCODE use16
GROUP KEYBOARD_GROUP KEYBOARD_CODE
global terminal_keyboard_dispatch_far,terminal_keyboard_dispatch_end
terminal_keyboard_dispatch_far:
%define _terminal_autostart_flush far keyboard_bank__terminal_autostart_flush
%define keyboard_poll far keyboard_bank_keyboard_poll
%define menu_pending_cancel far keyboard_bank_menu_pending_cancel
%define terminal_break_cancel far keyboard_bank_terminal_break_cancel
%define terminal_break_start far keyboard_bank_terminal_break_start
%define terminal_capture_crlf far keyboard_bank_terminal_capture_crlf
%define terminal_capture_flush far keyboard_bank_terminal_capture_flush
%define terminal_capture_pause far keyboard_bank_terminal_capture_pause
%define terminal_capture_toggle far keyboard_bank_terminal_capture_toggle
%define terminal_connection_cancel far keyboard_bank_terminal_connection_cancel
%define terminal_connection_exit far keyboard_bank_terminal_connection_exit
%define terminal_connection_start far keyboard_bank_terminal_connection_start
%define terminal_controller_key far keyboard_bank_terminal_controller_key
%define terminal_defer_key far keyboard_bank_terminal_defer_key
%define terminal_macro_cancel far keyboard_bank_terminal_macro_cancel
%define terminal_macro_start far keyboard_bank_terminal_macro_start
%define terminal_monitor_key far keyboard_bank_terminal_monitor_key
%define terminal_printer_toggle far keyboard_bank_terminal_printer_toggle
%define terminal_program_cancel far keyboard_bank_terminal_program_cancel
%define terminal_read_key far keyboard_bank_terminal_read_key
%define terminal_redisplay_key far keyboard_bank_terminal_redisplay_key
%define terminal_script_start far keyboard_bank_terminal_script_start
%define terminal_setup_start far keyboard_bank_terminal_setup_start
%define terminal_snapshot_start far keyboard_bank_terminal_snapshot_start
%define terminal_take_deferred_key far keyboard_bank_terminal_take_deferred_key
%define terminal_transfer_start far keyboard_bank_terminal_transfer_start
%define terminal_translation_edit_start far keyboard_bank_terminal_translation_edit_start
%define terminal_translation_reload_start far keyboard_bank_terminal_translation_reload_start
%define terminal_upload_start far keyboard_bank_terminal_upload_start
%endif
.keyboard:
%ifdef TERMINAL_MANUAL_INIT
 extern terminal_manual_init_active,terminal_manual_init_key_far
 cmp word [terminal_manual_init_active],0
 jne .bios_key
 extern terminal_recording_owned_far
 call far terminal_recording_owned_far
 or ax,ax
 jnz .bios_key ; A deferred Init must not starve the keys that stop recording.
 cmp word [connection_state],0
 je .manual_fifo_ready
 cmp word [connection_state],6
 jne .bios_key ; Dial/ACK waits still need their Escape/hangup/exit keys.
.manual_fifo_ready:
%endif
 cmp word [terminal_menu_pending],0
 jne .bios_key
 cmp word [terminal_macro_active],0
 jne .bios_key
 cmp word [terminal_program_pending],0
 jne .bios_key
 call terminal_take_deferred_key
 jnc .key_ready
.bios_key:
 call keyboard_poll
 or ax,ax
 jz .done
 ; A successful peek makes this actual blocking read immediately satisfiable;
 ; the private application queue is disabled and BIOS has one foreground reader.
 call terminal_read_key
.key_ready:
%ifdef TERMINAL_SOUND
 extern terminal_connect_alert_stop
 call far terminal_connect_alert_stop
%endif
 cmp word [terminal_menu_pending],0
 je .dispatch_key
 cmp ax,0x2c00
 je .done ; Repeated request/typematic is idempotent, not typeahead.
 cmp ax,0x2d00
 je .cancel_menu_then_dispatch
 cmp ax,0x2300
 je .cancel_menu_then_dispatch
 cmp al,27
 je .cancel_menu
 call terminal_defer_key
 cmp word [terminal_quit],0
 jne .cancel_menu
 jmp .done
.cancel_menu_then_dispatch:
 call menu_pending_cancel
 jmp .dispatch_key
.cancel_menu:
 call menu_pending_cancel
 jmp .done
.dispatch_key:
%ifdef TERMINAL_MANUAL_INIT
 call far terminal_manual_init_key_far
 jc .done
%endif
 push ax
 call _terminal_autostart_flush
 pop ax
 call terminal_redisplay_key
 jc .done
 cmp ax,0x3000 ; Native Alt-B, including dedicated/raw controller mode.
 je .break
 call terminal_controller_key
 jc .done
 call terminal_monitor_key
 jc .done
%ifdef TERMINAL_LOCAL_CONTROLS
 extern terminal_local_control_key
 call far terminal_local_control_key
 jc .done
%endif
 cmp ax,0x2200 ;Native Alt-G screen-file snapshot
 je .snapshot
 cmp ax,0x2600 ;Native Alt-L processed printer copy
 je .printer
 cmp ax,0x6800 ;Native Alt-F1 capture toggle
 je .capture
 cmp ax,0x6900 ;Native Alt-F2 capture hold
 je .capture_pause
 cmp ax,0x6a00 ;Native Alt-F3 CR-adds-LF
 je .capture_crlf
%ifdef TERMINAL_ORIGINAL_KEYS
 cmp ax,0xfa00 ; Source-owned menu action: receive. Alt-R owns recording.
%else
 cmp ax,0x1300 ;Alt-R: exclusive ordinaryXMODEM receive owner
%endif
 je .receive_file
%ifdef TERMINAL_ORIGINAL_KEYS
 cmp ax,0xf900 ; Source-owned menu action: send. Alt-S owns setup.
%else
 cmp ax,0x1f00 ;Alt-S: exclusive ordinaryXMODEM send owner
%endif
 je .send_file
 cmp ax,0x2d00
 je .quit
 cmp ax,0x2300 ; Alt-H: configured hang-up
 je .hangup
%ifdef TERMINAL_REFERENCE
 cmp ax,0xf600 ; Browser-only redial; Alt-D belongs to the directory chooser.
%else
 cmp ax,0x2000 ; Alt-D: repeat explicitly selected target
%endif
 je .redial
 cmp word [terminal_ansi_wait_active],0
 je .connection_key
 cmp al,27
 jne .done ; Original wait consumes other local keys without transmission.
 mov word [terminal_ansi_wait_cancel],1
 jmp .done
.connection_key:
 cmp word [connection_state],0
 je .terminal_key
 cmp word [connection_state],6
 je .terminal_key
 cmp al,27
 jne .done
 xor ax,ax
 call terminal_connection_cancel
 jmp .done
.terminal_key:
 cmp word [terminal_macro_active],0
 jne .defer
 cmp word [terminal_program_pending],0
 je .meta_key
.defer:
 cmp al,27
 je .cancel_macro
 call terminal_defer_key
 jmp .done
.cancel_macro:
 call terminal_macro_cancel
 call terminal_program_cancel
 jmp .done
.meta_key:
 cmp ax,0xfe00 ;Menu-only completed Script filename prompt.
 jne .script_not_selected
 call terminal_script_start
 jmp .done
.script_not_selected:
%ifdef TERMINAL_REFERENCE
 cmp ax,0x1100 ; Original Alt-W: translation table.
 je .translation_editor
 cmp ax,0xf700 ; Browser/private translation action; Alt-F8 is key mapping.
%else
 cmp ax,0x6f00 ;Alt-F8: maintained direct input-table editor.
%endif
 jne .reload_key
.translation_editor:
 call terminal_translation_edit_start
 jmp .done
.reload_key:
 cmp ax,0x7000 ;Alt-F9: maintained explicit same-table reload (native no-op).
 jne .settings_key
 call terminal_translation_reload_start
 jmp .done
.settings_key:
%ifdef TERMINAL_ORIGINAL_KEYS
 cmp ax,0x1f00 ; Original Alt-S: saved settings.
 je .setup
 cmp ax,0x1900 ; Original Alt-P: editor starts with the port field selected.
 je .setup
%endif
 cmp ax,0x7100 ;Alt-F10: direct maintained settings editor.
 jne .ordinary_meta
.setup:
 call terminal_setup_start
 jmp .done
.ordinary_meta:
 or al,al
 jnz .classify
 cmp ah,0x78
 jb .classify
 cmp ah,0x81
 ja .classify
 mov al,ah
 xor ah,ah
 sub ax,0x78
 call terminal_macro_start
 or ax,ax
 jz .done
 jmp .unsupported
.classify:
 mov bx,0xffff
%ifdef TERMINAL_ORIGINAL_KEYS
 push ax
%endif
 call far terminal_key_output
%ifdef TERMINAL_ORIGINAL_KEYS
 pop dx
%endif
 cmp word [terminal_quit],0
 jne .done
 or ax,ax
 jz .done
%ifdef TERMINAL_ORIGINAL_KEYS
 ; Keep assigned BBS page keys. Only the native local classification falls
 ; back to file transfer; invalid bindings/queue errors retain their errors.
 cmp ax,3
 jne .unsupported
 cmp dx,0x49e0
 je .send_file
 cmp dx,0x4900
 je .send_file
 cmp dx,0x51e0
 je .receive_file
 cmp dx,0x5100
 je .receive_file
%endif
.unsupported:
 ; A recognized original local command needs application UI/services that have
 ; not been reconstructed. Keep this explicit instead of transmitting the key.
 mov word [terminal_exit_code],4
 mov word [terminal_quit],1
 jmp .done
.break:
 call terminal_break_start
 jmp .done
.capture:
 call terminal_capture_toggle
 jmp .done
.printer:
 call terminal_printer_toggle
 jmp .done
.snapshot:
 call terminal_snapshot_start
 jmp .done
.capture_pause:
 call terminal_capture_pause
 jmp .done
.capture_crlf:
 call terminal_capture_crlf
 jmp .done
.receive_file:
 call terminal_capture_flush
 call terminal_transfer_start
 jmp .done
.send_file:
 call terminal_capture_flush
 call terminal_upload_start
 jmp .done
.quit:
 call terminal_macro_cancel
 call terminal_program_cancel
 call terminal_connection_exit
 jmp .done
.hangup:
 call terminal_macro_cancel
 call terminal_program_cancel
 mov ax,1
 call terminal_connection_cancel
 jmp .done
.redial:
 call terminal_break_cancel
 call terminal_macro_cancel
 call terminal_program_cancel
 cmp word [connection_state],0
 jne .done
 cmp byte [connection_enabled],0
 je .done
 call terminal_connection_start
.done:
%ifdef TERMINAL_KEYBOARD_BANK
 retf
terminal_keyboard_dispatch_end:
%undef _terminal_autostart_flush
%undef keyboard_poll
%undef menu_pending_cancel
%undef terminal_break_cancel
%undef terminal_break_start
%undef terminal_capture_crlf
%undef terminal_capture_flush
%undef terminal_capture_pause
%undef terminal_capture_toggle
%undef terminal_connection_cancel
%undef terminal_connection_exit
%undef terminal_connection_start
%undef terminal_controller_key
%undef terminal_defer_key
%undef terminal_macro_cancel
%undef terminal_macro_start
%undef terminal_monitor_key
%undef terminal_printer_toggle
%undef terminal_program_cancel
%undef terminal_read_key
%undef terminal_redisplay_key
%undef terminal_script_start
%undef terminal_setup_start
%undef terminal_snapshot_start
%undef terminal_take_deferred_key
%undef terminal_transfer_start
%undef terminal_translation_edit_start
%undef terminal_translation_reload_start
%undef terminal_upload_start
SEGMENT _TEXT
global menu_pending_cancel
%macro KEYBOARD_BRIDGE 1
 global keyboard_bank_%1
 keyboard_bank_%1:
 ; CALL/RETF preserve the callee's result registers and flags. No arguments
 ; live above the return address, and DS=SS is unchanged across the bank.
 call %1
 retf
%endmacro
KEYBOARD_BRIDGE _terminal_autostart_flush
KEYBOARD_BRIDGE keyboard_poll
KEYBOARD_BRIDGE menu_pending_cancel
KEYBOARD_BRIDGE terminal_break_cancel
KEYBOARD_BRIDGE terminal_break_start
KEYBOARD_BRIDGE terminal_capture_crlf
KEYBOARD_BRIDGE terminal_capture_flush
KEYBOARD_BRIDGE terminal_capture_pause
KEYBOARD_BRIDGE terminal_capture_toggle
KEYBOARD_BRIDGE terminal_connection_cancel
KEYBOARD_BRIDGE terminal_connection_exit
KEYBOARD_BRIDGE terminal_connection_start
KEYBOARD_BRIDGE terminal_controller_key
KEYBOARD_BRIDGE terminal_defer_key
KEYBOARD_BRIDGE terminal_macro_cancel
KEYBOARD_BRIDGE terminal_macro_start
KEYBOARD_BRIDGE terminal_monitor_key
KEYBOARD_BRIDGE terminal_printer_toggle
KEYBOARD_BRIDGE terminal_program_cancel
KEYBOARD_BRIDGE terminal_read_key
KEYBOARD_BRIDGE terminal_redisplay_key
KEYBOARD_BRIDGE terminal_script_start
KEYBOARD_BRIDGE terminal_setup_start
KEYBOARD_BRIDGE terminal_snapshot_start
KEYBOARD_BRIDGE terminal_take_deferred_key
KEYBOARD_BRIDGE terminal_transfer_start
KEYBOARD_BRIDGE terminal_translation_edit_start
KEYBOARD_BRIDGE terminal_translation_reload_start
KEYBOARD_BRIDGE terminal_upload_start
%else
 pop es
 pop di
 pop si
 pop bp
 ret
%endif

; No macro execution state is changed: only the pending menu's typeahead is
; discarded. Escape remains local; Alt-X/Alt-H continue through normal dispatch.
menu_pending_cancel:
 mov word [terminal_menu_pending],0
 mov word [terminal_deferred_count],0
 mov word [terminal_deferred_head],0
 mov word [terminal_deferred_tail],0
 ret

; Private resident request service. Preserve AX and the ordinary key ABI;
; dispatch the actual Alt-Z only after parsing yields and no view owns keys.
terminal_menu_pending_poll:
 push ax
 cmp word [terminal_menu_pending],0
 je .done
 cmp word [terminal_parser_active],0
 jne .done
 cmp word [_redisplay_active],0
 jne .cancel
 mov ax,0x2c00
 call terminal_redisplay_key
 cmp word [_command_menu_active],0
 je .cancel
 mov word [terminal_menu_pending],0
 jmp .done
.cancel:
 call menu_pending_cancel
.done:
 pop ax
 ret

; UART/modem/TX service without consuming a BIOS key. Used by capture prompt.
global terminal_poll_serial
terminal_poll_serial:
%ifdef TERMINAL_TRAPS
 extern terminal_trap_poll
 call far terminal_trap_poll
%endif
 cmp word [terminal_aspect_active],0
 je .ordinary
 call far terminal_render_poll
 ret
.ordinary:
 push bp
 push si
 push di
 push es
 cmp word [terminal_quit],0
 jne .done
 call terminal_connection_poll
%ifdef TERMINAL_AUTO_ANSWER
 extern terminal_auto_answer_ui_poll_far
 call far terminal_auto_answer_ui_poll_far
%endif
 cmp word [terminal_quit],0
 jne .done
 call terminal_break_poll
 call uart_poll_flow
 mov word [terminal_macro_tx_allowed],0
%ifdef TERMINAL_MANUAL_INIT
 extern terminal_manual_init_poll_far,terminal_manual_init_sync_far
 cmp word [terminal_manual_init_active],0
 je .manual_idle
 mov ax,1
 call far terminal_manual_init_poll_far
 call far terminal_manual_init_sync_far
 jmp .macro ; Never lend this same poll's physical-write grant to ordinary TX.
.manual_idle:
%endif
 cmp word [connection_state],0
 je .transmit
 cmp word [connection_state],6
 jne .macro
.transmit:
 cmp word [terminal_tx_count],0
 je .grant_macro
 mov bx,[terminal_tx_head]
 mov al,[terminal_tx_buffer+bx]
 call uart_try_write
 jc .macro
 mov bx,[terminal_tx_head]
 call far terminal_tx_origin_delivered_far
 ; try_write preserves AX/DX; keep head lookup independent of future API changes.
 mov bx,[terminal_tx_head]
 inc bx
 and bx,1023
 mov [terminal_tx_head],bx
 dec word [terminal_tx_count]
 cmp word [terminal_clipboard_remaining],0
 je .clipboard_done
 dec word [terminal_clipboard_remaining]
.clipboard_done:
 inc word [terminal_macro_tx_epoch]
 jmp .macro
.grant_macro:
 mov word [terminal_macro_tx_allowed],1
.macro:
 call terminal_macro_poll
 cmp word [terminal_quit],0
 jne .done
 .done:
 pop es
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
global terminal_tx_head,terminal_tx_tail,terminal_tx_count,terminal_tx_buffer
terminal_tx_head: dw 0
terminal_tx_tail: dw 0
terminal_tx_count: dw 0
terminal_tx_buffer: times 1024 db 0
