; Interactive maintained DOS host for the recovered PCPlus terminal engine.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern terminal_parse_options,terminal_usage,terminal_stack_top
extern terminal_poll_io,terminal_quit,terminal_exit_code,terminal_tx_count
extern terminal_receive_character,csi_clear_tabs,terminal_clear_home
extern terminal_break_cancel
extern uart_save_hardware_state,uart_restore_hardware_state
extern uart_disable,uart_enable,uart_install_interrupt,uart_restore_interrupt
extern uart_clear_receive_buffer,uart_set_baud_divisor,uart_set_line_control
extern uart_receive_byte,uart_rx_dropped,uart_port_rbr
extern terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits
extern terminal_irq_vector,terminal_port_number,csi_unimplemented_service
extern screen_attribute_cells,erase_attribute_values,erase_shadow_cells
extern terminal_history_buffer
extern terminal_redisplay_before,terminal_redisplay_idle,terminal_redisplay_stop
extern _redisplay_search_pending,_redisplay_export_pending
extern _history_file_event
extern terminal_run_startup_setup
extern _terminal_autostart_initialize,_terminal_autostart_flush
extern _terminal_autostart_poll,_terminal_autostart_input
extern terminal_setup_bind
extern terminal_load_configuration
extern terminal_select_directory
extern terminal_directory_flush_accounting
extern terminal_load_keyboard
extern terminal_load_translation,terminal_receive_input
extern terminal_load_actions,terminal_macro_cancel
extern terminal_program_initialize,terminal_program_poll,terminal_program_cancel,terminal_program_pending
extern terminal_reset_capture
extern terminal_release_flow,terminal_cleanup_flow_failed
extern terminal_transfer_poll,terminal_transfer_filter,terminal_transfer_shutdown
extern _terminal_transfer_initialize
extern _terminal_upload_initialize
extern _terminal_batch_initialize
extern _capture_session_initialize,_capture_session_shutdown
extern _recording_terminal_initialize,_recording_terminal_shutdown
extern terminal_capture_poll
extern _snapshot_file_initialize,terminal_snapshot_shutdown
extern _monitor_file_initialize,terminal_monitor_poll,terminal_monitor_filter
extern terminal_monitor_active,terminal_monitor_shutdown
extern _printer_device_initialize,terminal_printer_poll
extern terminal_printer_receive_hold,terminal_printer_shutdown
extern terminal_controller_poll,terminal_controller_filter
extern terminal_controller_receive_hold,terminal_controller_shutdown
extern terminal_connection_start,terminal_connection_receive
extern connection_state,connection_result
extern terminal_status_poll
; Open Watcom small-code consistency marker for the near-C DOS IO subset.
global _small_code_
_small_code_:
..start:
 mov ax,es
 mov bx,DGROUP
 mov ds,bx
 cli
 mov ss,bx
 mov sp,terminal_stack_top
 sti
 cld
%ifdef TERMINAL_MOUSE
 extern _terminal_mouse_bootstrap,_terminal_mouse_start,terminal_mouse_exit
 push ax
 call _terminal_mouse_bootstrap
 pop ax
%endif
 push ax ;PSP segment remains the PROGRAM initializer input.
 call _terminal_autostart_initialize
 pop ax
 call terminal_program_initialize
 push ax
 call _terminal_transfer_initialize
 call _terminal_upload_initialize
 call _terminal_batch_initialize
 call _capture_session_initialize
 call far _recording_terminal_initialize
 call _snapshot_file_initialize
 call _monitor_file_initialize
 xor ax,ax
 push ax
 push ax
 mov ax,2
 push ax
 call _history_file_event
 add sp,6
 call _printer_device_initialize
 pop ax
%ifdef TERMINAL_EXIT_GUARD
 extern terminal_exit_guard_begin,terminal_exit_guard_finish
 call far terminal_exit_guard_begin
 jc terminal_shutdown
%endif
%ifdef TERMINAL_TRAPS
 extern terminal_trap_open,terminal_trap_close,terminal_trap_poll
 push ax
 call far terminal_trap_open
 or ax,ax
 pop ax
 jnz terminal_shutdown
%endif
 call terminal_parse_options
 jnc .configured
 cmp ax,1
 jne .bad_options
 mov word [terminal_exit_code],0
 jmp .usage
.bad_options:
 mov word [terminal_exit_code],1
.usage:
%ifdef TERMINAL_FAR_USAGE
 push ds
 mov ax,seg terminal_usage
 mov ds,ax
%endif
 mov dx,terminal_usage
 mov ah,9
 int 0x21
%ifdef TERMINAL_FAR_USAGE
 pop ds
%endif
 jmp terminal_shutdown
.configured:
 call terminal_select_directory
%ifdef TERMINAL_TRAPS
 call far terminal_trap_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
%endif
 or ax,ax
 jz .load_configuration
 cmp ax,1
 jne .configuration_error
 mov word [terminal_exit_code],0
 jmp terminal_shutdown
.load_configuration:
 call terminal_run_startup_setup
 or ax,ax
 jnz .configuration_error
 call terminal_load_configuration
 or ax,ax
 jnz .configuration_error
 call terminal_load_keyboard
 or ax,ax
 jnz .configuration_error
 call terminal_load_actions
 or ax,ax
 jnz .configuration_error
 call terminal_load_translation
 or ax,ax
 jnz .configuration_error
 call terminal_setup_bind
%ifdef TERMINAL_SPECIAL_EDITION
 extern terminal_special_splash
 call far terminal_special_splash
%endif
%ifdef TERMINAL_HOOK_INPUT_PROBE
 extern _terminal_hook_input_probe
 call far _terminal_hook_input_probe
 mov [terminal_exit_code],ax
 jmp terminal_shutdown
%endif
%ifdef TERMINAL_HOOK_PROBE
 ; Private diagnostic after normal startup, before UART/mouse acquisition.
 extern _terminal_hook_probe
 call far _terminal_hook_probe
 mov [terminal_exit_code],ax
 jmp terminal_shutdown
%endif
%ifdef TERMINAL_SESSION_PROJECTION_PROBE
 ; Source-built diagnostic only: observe projection after genuine startup
 ; configuration and before mouse/UART ownership. Normal product has no call.
 extern terminal_session_projection_probe_far
 call far terminal_session_projection_probe_far
 mov [terminal_exit_code],ax
 jmp terminal_shutdown
%endif
%ifdef TERMINAL_MOUSE
 call _terminal_mouse_start
 or ax,ax
 jnz .configuration_error
%endif
%ifdef TERMINAL_TRAPS
 call far terminal_trap_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
%endif
 ; Require a standard BIOS-listed serial port before changing its registers.
 mov bx,[terminal_port_number]
 dec bx
 shl bx,1
 mov ax,0x40
 mov es,ax
 mov ax,[es:bx]
 cmp ax,[uart_port_rbr]
 jne .missing_port
 or ax,ax
 jz .missing_port
 call uart_save_hardware_state
 mov byte [hardware_active],1
 call uart_disable
 push word [terminal_irq_vector]
 call uart_install_interrupt
 add sp,2
 mov byte [vector_active],1
 call uart_clear_receive_buffer
 push word [terminal_baud_high]
 push word [terminal_baud_low]
 call uart_set_baud_divisor
 add sp,4
 push word [terminal_stop_bits]
 push word [terminal_data_bits]
 push word [terminal_parity]
 call uart_set_line_control
 add sp,6
 ; Initialize owned metadata planes; DOS does not promise zeroed BSS.
 mov ax,ds
 mov es,ax
 xor ax,ax
 mov di,screen_attribute_cells
 mov cx,2048
 rep stosw
 mov di,erase_attribute_values
 mov cx,2048
 rep stosw
 mov ax,seg erase_shadow_cells
 mov es,ax
 xor ax,ax
 mov di,erase_shadow_cells
 ; Separate native shadow and full63000-byte history segments.
 mov cx,4096
 rep stosw
 mov ax,seg terminal_history_buffer
 mov es,ax
 xor ax,ax
 mov di,terminal_history_buffer
 mov cx,31500
 rep stosw
 push ds
 pop es
 mov ax,3
 int 0x10
 mov ax,1
 push ax
 call csi_clear_tabs
 add sp,2
 call terminal_clear_home
 call terminal_reset_capture
 or ax,ax
 jz .reset_ready
 mov ax,0x20a4
 jmp terminal_abort
.reset_ready:
 call uart_enable
 call terminal_connection_start
.loop:
%ifdef TERMINAL_TRAPS
 call far terminal_trap_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
%endif
%ifdef TERMINAL_TRAP_PROBE
 extern terminal_trap_probe_poll
 call far terminal_trap_probe_poll
%endif
 call _terminal_autostart_poll
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne terminal_shutdown
 call terminal_capture_poll
 call terminal_printer_poll
 call terminal_controller_poll
 call terminal_monitor_poll
 call terminal_transfer_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
 call terminal_program_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
 cmp word [terminal_program_pending],0
 jne .idle
 call far terminal_status_poll
 cmp word [uart_rx_dropped],0
 jne .overflow
 ; Leave post-match bytes in the actual RX ring while final command pacing
 ; finishes. A fast CONNECT+banner burst must not lose its first data bytes.
 cmp word [connection_state],2
 jne .receive
 cmp word [connection_result],0xffff
 jne .idle
.receive:
 cmp word [terminal_monitor_active],2
 je .idle ;Prompt owns keyboard; leave all incoming bytes in actual RX ring.
 call terminal_controller_receive_hold
 or ax,ax
 jnz .idle
 call terminal_printer_receive_hold
 or ax,ax
 jnz .idle ;Reserve two queue slots for native CR plus optional LF.
 call uart_receive_byte
 cmp ax,0xffff
 je .idle
 call terminal_redisplay_before
 call terminal_connection_receive
 jc .loop
 call terminal_monitor_filter
 jc .loop
 call terminal_controller_filter
 jc .loop
 call terminal_transfer_filter
 jc .loop
 push ax
 call _terminal_autostart_input
 add sp,2
 jmp .loop
.idle:
 call terminal_redisplay_idle
 cmp word [_redisplay_search_pending],0
 jne .loop
 cmp word [_redisplay_export_pending],0
 jne .loop
 cmp word [terminal_tx_count],0
 jne .loop
 sti
 hlt
 jmp .loop
.overflow:
 mov word [terminal_exit_code],6
 jmp terminal_shutdown
.missing_port:
 mov dx,missing_port
 mov ah,9
 int 0x21
 mov word [terminal_exit_code],5
 jmp terminal_shutdown
.configuration_error:
 mov dx,configuration_argument
%ifdef TERMINAL_MOUSE
 cmp ax,15
%else
 cmp ax,14
%endif
 ja .configuration_message
 mov bx,ax
 dec bx
 shl bx,1
 mov dx,[configuration_messages+bx]
.configuration_message:
 mov ah,9
 int 0x21
 mov word [terminal_exit_code],7
 jmp terminal_shutdown

global terminal_abort,terminal_shutdown
extern terminal_aspect_active,terminal_render_unsupported,terminal_render_typed_abort
terminal_abort:
 cmp word [terminal_aspect_active],0
 je .ordinary
 jmp far terminal_render_unsupported
.ordinary:
 ; Reached by explicit unsupported-service boundaries at arbitrary call depth.
 mov [csi_unimplemented_service],ax
 mov word [terminal_exit_code],2
terminal_shutdown:
 cmp word [terminal_aspect_active],0
 je .ordinary
 mov ax,10
 jmp far terminal_render_typed_abort
.ordinary:
 ; Discard parser/renderer frames, then unwind only resources actually acquired.
 cli
 mov ax,DGROUP
 mov ds,ax
 mov ss,ax
 mov sp,terminal_stack_top
 sti
 call _terminal_autostart_flush
 call terminal_redisplay_stop
 call terminal_break_cancel
 call terminal_macro_cancel
 call terminal_program_cancel
 call terminal_controller_shutdown
 call terminal_printer_shutdown
 or ax,ax
 jz .printer_closed
 cmp word [terminal_exit_code],0
 jne .printer_message
 mov word [terminal_exit_code],12
.printer_message:
 mov dx,printer_failed
 mov ah,9
 int 0x21
.printer_closed:
 cmp byte [hardware_active],0
 je .exit
 call terminal_release_flow
 call uart_disable
 cmp byte [vector_active],0
 je .restore
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
.restore:
 call uart_restore_hardware_state
 mov byte [hardware_active],0
.exit:
 call terminal_transfer_shutdown
 call terminal_monitor_shutdown
 or ax,ax
 jz .monitor_closed
 cmp word [terminal_exit_code],0
 jne .monitor_message
 mov word [terminal_exit_code],12
.monitor_message:
 mov dx,monitor_failed
 mov ah,9
 int 0x21
.monitor_closed:
 call terminal_snapshot_shutdown
 or ax,ax
 jz .snapshot_closed
 cmp word [terminal_exit_code],0
 jne .snapshot_message
 mov word [terminal_exit_code],12
.snapshot_message:
 mov dx,snapshot_failed
 mov ah,9
 int 0x21
.snapshot_closed:
 xor ax,ax
 push ax
 push ax
 mov ax,2
 push ax
 call _history_file_event
 add sp,6
 cmp ax,8 ; Only write/close/overflow/recovery failures affect final status.
 jb .history_closed
 cmp word [terminal_exit_code],0
 jne .history_message
 mov word [terminal_exit_code],12
.history_message:
 mov dx,history_failed
 mov ah,9
 int 0x21
.history_closed:
 call _capture_session_shutdown
 or ax,ax
 jz .capture_closed
 cmp word [terminal_exit_code],0
 jne .capture_message
 mov word [terminal_exit_code],12
.capture_message:
 mov dx,capture_failed
 mov ah,9
 int 0x21
.capture_closed:
 call far _recording_terminal_shutdown
 or ax,ax
 jz .recording_closed
 cmp word [terminal_exit_code],0
 jne .recording_closed
 mov word [terminal_exit_code],12
.recording_closed:
 call terminal_directory_flush_accounting
 or ax,ax
 jz .application_error
 mov dx,accounting_failed
 mov ah,9
 int 0x21
.application_error:
 cmp word [terminal_cleanup_flow_failed],0
 je .macro_error
 mov dx,flow_cleanup_failed
 mov ah,9
 int 0x21
.macro_error:
 cmp word [terminal_exit_code],10
 jne .keyboard_error
 mov dx,macro_failed
 mov ah,9
 int 0x21
 jmp .dos_exit
.keyboard_error:
 cmp word [terminal_exit_code],4
 jne .terminal_error
 mov dx,unsupported_keyboard
 mov ah,9
 int 0x21
 jmp .dos_exit
.terminal_error:
 cmp word [terminal_exit_code],2
 jne .dos_exit
 mov dx,unsupported
 mov ah,9
 int 0x21
.dos_exit:
%ifdef TERMINAL_MOUSE
 call far terminal_mouse_exit
%endif
%ifdef TERMINAL_TRAPS
 %ifdef TERMINAL_TRAP_PROBE
 extern terminal_trap_probe_closing,terminal_trap_probe_report
 call far terminal_trap_probe_closing
 %endif
 call far terminal_trap_close
 %ifdef TERMINAL_TRAP_PROBE
 call far terminal_trap_probe_report
 %endif
%endif
%ifdef TERMINAL_EXIT_GUARD
 call far terminal_exit_guard_finish
%endif
 mov ax,[terminal_exit_code]
 mov ah,0x4c
 int 0x21

SEGMENT _DATA public align=16 class=DATA use16
global terminal_parser_active
terminal_parser_active: dw 0
global hardware_active,vector_active
hardware_active: db 0
vector_active: db 0
missing_port: db 'Selected COM port is not listed by the BIOS.',13,10,'$'
unsupported: db 13,10,'Unsupported terminal function; terminal stopped.',13,10,'$'
unsupported_keyboard: db 13,10,'Unsupported keyboard binding or local command; terminal stopped.',13,10,'$'
history_failed: db 13,10,'History file could not be completed. Partial output may remain.',13,10,'$'
flow_cleanup_failed: db 13,10,'Could not resume software flow before exit.',13,10,'$'
macro_failed: db 13,10,'TEXT action timed out; terminal stopped.',13,10,'$'
accounting_failed: db 13,10,'Call statistics save needs attention. Check directory recovery files.',13,10,'$'
capture_failed: db 13,10,'Capture failed; partial log retained. Check free space and file access.',13,10,'$'
snapshot_failed: db 13,10,'Screen snapshot failed; partial file retained.',13,10,'$'
monitor_failed: db 13,10,'Monitor dump failed; partial file retained.',13,10,'$'
printer_failed: db 13,10,'Printer failed; output may be incomplete.',13,10,'$'
configuration_messages: dw configuration_io,configuration_serial,configuration_flow
 dw configuration_profile,configuration_display,configuration_argument,configuration_modem
 dw configuration_directory
 dw configuration_keyboard
 dw configuration_actions
 dw configuration_setup
 dw configuration_translation
 dw configuration_clipboard
 dw configuration_transfer
%ifdef TERMINAL_MOUSE
 dw configuration_mouse
configuration_mouse: db 'Could not apply mouse settings. Scales must be 1..999.',13,10,'$'
%endif
configuration_transfer: db 'Invalid download directory in configuration.',13,10,'$'
configuration_clipboard: db 'Configuration clipboard separator must be 0..255.',13,10,'$'
configuration_translation: db 'Invalid input translation mode or 256-byte XLT table.',13,10,'$'
configuration_setup: db 'Could not run PRMEDIT setup successfully. Check PRMEDIT.EXE and the PRM file.',13,10,'$'
configuration_io: db 'Could not read the requested PCPLUS 2.01 configuration.',13,10,'$'
configuration_serial: db 'Configuration has unsupported serial port or line settings.',13,10,'$'
configuration_flow: db 'Configuration flow-control values must be 0 or 1.',13,10,'$'
configuration_profile: db 'Configuration terminal profile must be ANSI or VT220.',13,10,'$'
configuration_display: db 'Configuration has unsupported display settings.',13,10,'$'
configuration_argument: db 'Invalid configuration request.',13,10,'$'
configuration_modem: db 'Dialing requires a valid explicit modem configuration.',13,10,'$'
configuration_directory: db 'Could not select a supported directory entry.',13,10,'$'
configuration_keyboard: db 'Could not load a valid keyboard profile from the requested KBD file.',13,10,'$'
configuration_actions: db 'Could not load valid actions from the requested KEY file.',13,10,'$'
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
