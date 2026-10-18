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
..start:
 mov ax,es
 mov bx,DGROUP
 mov ds,bx
 cli
 mov ss,bx
 mov sp,terminal_stack_top
 sti
 cld
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
 mov di,erase_shadow_cells
 mov cx,4096
 rep stosw
 mov ax,3
 int 0x10
 mov ax,1
 push ax
 call csi_clear_tabs
 add sp,2
 call terminal_clear_home
 call uart_enable
.loop:
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne terminal_shutdown
 cmp word [uart_rx_dropped],0
 jne .overflow
 call uart_receive_byte
 cmp ax,0xffff
 je .idle
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
 cmp byte [hardware_active],0
 je .exit
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
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
