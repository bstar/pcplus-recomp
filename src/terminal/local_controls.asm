; Foreground local Clear/Reset/Duplex owner. Optional; no UART transmission.
BITS 16
CPU 8086
%ifdef TERMINAL_LOCAL_CONTROLS
SEGMENT _TEXT public class=CODE use16
extern terminal_clear_home,local_reset_1368,local_duplex_3316,terminal_defer_key
global terminal_control_clear_far,terminal_control_reset_far,terminal_control_duplex_far,terminal_control_defer_far
terminal_control_clear_far:
 call terminal_clear_home
 retf
terminal_control_reset_far:
 call local_reset_1368
 retf
terminal_control_duplex_far:
 call local_duplex_3316
 retf
terminal_control_defer_far:
 call terminal_defer_key
 retf

SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern terminal_parser_active,terminal_macro_active,terminal_program_pending,terminal_program_active
extern terminal_transfer_pending,terminal_transfer_active,terminal_aspect_active
extern terminal_ansi_wait_active,terminal_snapshot_active,uart_break_hold,connection_state
extern _redisplay_active,_command_menu_active,reset_ready
extern terminal_monitor_active,terminal_controller_active
extern terminal_browser_screen_owned,terminal_editor_screen_owned
%ifdef TERMINAL_SCREEN_PAUSE
extern terminal_screen_pause,terminal_screen_pause_active
%endif
%ifdef TERMINAL_ELAPSED_VIEW
extern _terminal_elapsed_view_active
%endif
global terminal_local_control_key
; AX normalized BIOS key. CF1 consumed/deferred; CF0 unrelated, AX unchanged.
; Existing FIFO preserves key order while parsing/other owners are active.
terminal_local_control_key:
%ifdef TERMINAL_ELAPSED_VIEW
 ; A visible elapsed window consumes every dismissal key in its own owner.
 cmp word [_terminal_elapsed_view_active],0
 je .classify
 clc
 retf
.classify:
 cmp ax,0x1400
 je .selected
%endif
%ifdef TERMINAL_STATUS_CONTROL
 cmp al,29 ; Normalize Ctrl-] by character, like the reference menu.
 je .selected
%endif
 cmp ax,0x2e00
 je .selected
%ifdef TERMINAL_MANUAL_INIT
 cmp ax,0x2400
 je .selected
%ifdef TERMINAL_AUTO_ANSWER
 cmp ax,0x1500
 je .selected
%endif
%endif
 cmp ax,0x1600
 je .selected
 cmp ax,0x1200
 je .selected
%ifdef TERMINAL_SCREEN_PAUSE
 cmp ax,0x3100
 je .selected
%endif
 clc
 retf
.selected:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov bx,[terminal_parser_active]
 or bx,[terminal_macro_active]
 or bx,[terminal_program_pending]
 or bx,[terminal_program_active]
 or bx,[terminal_transfer_pending]
 or bx,[terminal_transfer_active]
 or bx,[terminal_aspect_active]
 or bx,[terminal_ansi_wait_active]
 or bx,[terminal_snapshot_active]
 or bx,[uart_break_hold]
 or bx,[_redisplay_active]
 or bx,[_command_menu_active]
 or bx,[terminal_monitor_active]
 or bx,[terminal_controller_active]
%ifdef TERMINAL_SCREEN_PAUSE
 or bx,[terminal_screen_pause_active]
%endif
 jnz .defer
 cmp byte [terminal_browser_screen_owned],0
 jne .defer
 cmp byte [terminal_editor_screen_owned],0
 jne .defer
 cmp word [connection_state],0
 je .admitted
 cmp word [connection_state],6
 jne .defer
.admitted:
 mov word [terminal_local_control_status],0
%ifdef TERMINAL_STATUS_CONTROL
 cmp al,29
 je .status
%endif
%ifdef TERMINAL_MANUAL_INIT
 cmp ax,0x2400
 je .initialize
%ifdef TERMINAL_AUTO_ANSWER
 cmp ax,0x1500
 je .initialize
%endif
%endif
%ifdef TERMINAL_ELAPSED_VIEW
 cmp ax,0x1400
 je .view_admitted
%endif
%ifdef TERMINAL_SCREEN_PAUSE
 cmp ax,0x3100
 je .pause
%endif
 cmp ax,0x2e00
 jne .reset
 call far terminal_control_clear_far
 jmp .done
.reset:
 cmp ax,0x1600
 jne .duplex
 cmp word [reset_ready],1
 jne .not_ready
 call far terminal_control_reset_far
 jmp .done
.duplex:
 call far terminal_control_duplex_far
 jmp .done
%ifdef TERMINAL_SCREEN_PAUSE
.pause:
 call terminal_screen_pause
 jmp .done
%endif
%ifdef TERMINAL_STATUS_CONTROL
.status:
 extern _terminal_status_toggle
 call far _terminal_status_toggle
 mov [terminal_local_control_status],ax
 jmp .done
%endif
.not_ready:
 mov word [terminal_local_control_status],2
 jmp .done
%ifdef TERMINAL_MANUAL_INIT
.initialize:
 extern terminal_recording_owned_far,terminal_manual_init_configured_far
 extern terminal_tx_count,terminal_menu_pending
 push ax
 call far terminal_recording_owned_far
 mov bx,ax
 pop ax
 or bx,[terminal_tx_count]
 or bx,[terminal_menu_pending]
 jnz .defer
%ifdef TERMINAL_AUTO_ANSWER
 cmp ax,0x1500
 jne .init_only
 extern terminal_auto_answer_admit_far,terminal_auto_answer_configured_far
 call far terminal_auto_answer_admit_far
 or ax,ax
 jnz .not_ready
 call far terminal_auto_answer_configured_far
 jmp .done
.init_only:
%endif
 call far terminal_manual_init_configured_far
 jmp .done
%endif
.defer:
 mov word [terminal_local_control_status],1
 call far terminal_control_defer_far
%ifdef TERMINAL_ELAPSED_VIEW
 jmp .done
%endif
%ifdef TERMINAL_ELAPSED_VIEW
.view_admitted:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 clc
 retf
%endif
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 stc
 retf
SEGMENT _DATA public class=DATA use16
global terminal_local_control_status
terminal_local_control_status: dw 0 ;0 executed,1 deferred,2 baseline absent; status owner3/4 refused/rollback
%ifndef TERMINAL_SPECIAL_EDITION
; The Special Edition splash supplies this alignment anchor in that variant.
; Other reference builds need the same independent C near-pointer base.
SEGMENT REFERENCE_CODE public align=16 class=FARCODE use16
GROUP REFERENCE_GROUP REFERENCE_CODE
%endif
%endif
