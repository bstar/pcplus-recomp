; Foreground-only services for CONFIG_CODE invitation ownership.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _terminal_transfer_preferences
extern terminal_receive_input,terminal_clock_ticks,terminal_transfer_start
extern terminal_transfer_pending,terminal_transfer_active,terminal_transfer_protocol
extern terminal_transfer_direction,terminal_transfer_filename,terminal_transfer_automatic
extern terminal_quit,uart_rx_mask,uart_software_flow,uart_break_hold
extern terminal_monitor_active,terminal_controller_active,connection_state
extern terminal_program_pending,terminal_program_active,terminal_macro_active
extern terminal_tab_wrap,terminal_control_mode_9026,terminal_newline_mode_9020
extern terminal_parser_active,terminal_ansi_wait_active
global _terminal_auto_deliver,_terminal_auto_allowed,_terminal_auto_start,_terminal_auto_ticks
extern terminal_recording_owned_far
_terminal_auto_ticks:
 jmp terminal_clock_ticks
_terminal_auto_deliver:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,[bp+4]
 call terminal_receive_input
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_terminal_auto_allowed:
 call far terminal_recording_owned_far
 or ax,ax
 jnz .no
 xor ax,ax
 cmp word [_terminal_transfer_preferences],0
 je .done
 cmp word [uart_rx_mask],255
 jne .done
 cmp word [uart_software_flow],0
 jne .done
 mov ax,[terminal_quit]
 or ax,[uart_break_hold]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 or ax,[terminal_macro_active]
 or ax,[terminal_tab_wrap]
 or ax,[terminal_control_mode_9026]
 or ax,[terminal_newline_mode_9020]
 or ax,[terminal_parser_active]
 or ax,[terminal_ansi_wait_active]
 jnz .no
 cmp word [connection_state],0
 je .yes
 cmp word [connection_state],6
 jne .no
.yes:mov ax,1
 ret
.no:xor ax,ax
.done:ret
_terminal_auto_start:
 push bp
 push bx
 push si
 push di
 push es
 call _terminal_auto_allowed
 or ax,ax
 jz .done
 call terminal_transfer_start
 mov ax,[terminal_transfer_pending]
 or ax,ax
 jz .done
 mov word [terminal_transfer_protocol],2
 mov word [terminal_transfer_direction],0
 mov word [terminal_transfer_automatic],1
 push ds
 pop es
 cld
 mov si,_terminal_transfer_preferences+2
 mov di,terminal_transfer_filename
 mov cx,32
 rep movsw
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
