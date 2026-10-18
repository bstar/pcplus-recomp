; Interactive maintained DOS host for the recovered PCPlus terminal engine.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern terminal_parse_options,terminal_usage,terminal_stack_top
extern terminal_poll_io,terminal_quit,terminal_exit_code,terminal_tx_count
extern terminal_receive_character,csi_clear_tabs,terminal_clear_home
extern uart_save_hardware_state,uart_restore_hardware_state
extern uart_disable,uart_enable,uart_install_interrupt,uart_restore_interrupt
extern uart_clear_receive_buffer,uart_set_baud_divisor,uart_set_line_control
extern uart_receive_byte,uart_rx_dropped,uart_port_rbr
extern terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits
extern terminal_irq_vector,terminal_port_number,csi_unimplemented_service
extern screen_attribute_cells,erase_attribute_values,erase_shadow_cells
extern terminal_load_configuration
extern terminal_select_directory
extern terminal_directory_flush_accounting
extern terminal_load_keyboard
extern terminal_load_actions,terminal_macro_cancel
extern terminal_program_initialize,terminal_program_poll,terminal_program_cancel,terminal_program_pending
extern terminal_reset_capture
extern terminal_release_flow,terminal_cleanup_flow_failed
extern terminal_transfer_poll,terminal_transfer_filter,terminal_transfer_shutdown
extern _terminal_transfer_initialize
extern terminal_connection_start,terminal_connection_receive
extern connection_state,connection_result
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
 call terminal_program_initialize
 push ax
 call _terminal_transfer_initialize
 pop ax
 call terminal_parse_options
 jnc .configured
 cmp ax,1
 jne .bad_options
 mov word [terminal_exit_code],0
 jmp .usage
.bad_options:
 mov word [terminal_exit_code],1
.usage:
 mov dx,terminal_usage
 mov ah,9
 int 0x21
 jmp terminal_shutdown
.configured:
 call terminal_select_directory
 or ax,ax
 jz .load_configuration
 cmp ax,1
 jne .configuration_error
 mov word [terminal_exit_code],0
 jmp terminal_shutdown
.load_configuration:
 call terminal_load_configuration
 or ax,ax
 jnz .configuration_error
 call terminal_load_keyboard
 or ax,ax
 jnz .configuration_error
 call terminal_load_actions
 or ax,ax
 jnz .configuration_error
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
 ; FAR_STORAGE is contiguous8192-byte shadow plus4096-byte history.
 mov cx,6144
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
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne terminal_shutdown
 call terminal_transfer_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
 call terminal_program_poll
 cmp word [terminal_quit],0
 jne terminal_shutdown
 cmp word [terminal_program_pending],0
 jne .idle
 cmp word [uart_rx_dropped],0
 jne .overflow
 ; Leave post-match bytes in the actual RX ring while final command pacing
 ; finishes. A fast CONNECT+banner burst must not lose its first data bytes.
 cmp word [connection_state],2
 jne .receive
 cmp word [connection_result],0xffff
 jne .idle
.receive:
 call uart_receive_byte
 cmp ax,0xffff
 je .idle
 call terminal_connection_receive
 jc .loop
 call terminal_transfer_filter
 jc .loop
 push ax
 call terminal_receive_character
 add sp,2
 jmp .loop
.idle:
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
 cmp ax,10
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
terminal_abort:
 ; Reached by explicit unsupported-service boundaries at arbitrary call depth.
 mov [csi_unimplemented_service],ax
 mov word [terminal_exit_code],2
terminal_shutdown:
 ; Discard parser/renderer frames, then unwind only resources actually acquired.
 cli
 mov ax,DGROUP
 mov ds,ax
 mov ss,ax
 mov sp,terminal_stack_top
 sti
 call terminal_macro_cancel
 call terminal_program_cancel
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
 mov ax,[terminal_exit_code]
 mov ah,0x4c
 int 0x21

SEGMENT _DATA public align=16 class=DATA use16
hardware_active: db 0
vector_active: db 0
missing_port: db 'Selected COM port is not listed by the BIOS.',13,10,'$'
unsupported: db 13,10,'Unsupported terminal function; terminal stopped.',13,10,'$'
unsupported_keyboard: db 13,10,'Unsupported keyboard binding or local command; terminal stopped.',13,10,'$'
flow_cleanup_failed: db 13,10,'Could not resume software flow before exit.',13,10,'$'
macro_failed: db 13,10,'TEXT action timed out; terminal stopped.',13,10,'$'
accounting_failed: db 13,10,'Call statistics save needs attention. Check directory recovery files.',13,10,'$'
configuration_messages: dw configuration_io,configuration_serial,configuration_flow
 dw configuration_profile,configuration_display,configuration_argument,configuration_modem
 dw configuration_directory
 dw configuration_keyboard
 dw configuration_actions
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
