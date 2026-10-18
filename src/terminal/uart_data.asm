; Independent small-model data layout. No original binary data is embedded.
BITS 16
CPU 8086
SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA _BSS STACK
%macro wordvar 2
 global %1
 %1: dw %2
%endmacro
%macro bytevar 2
 global %1
 %1: db %2
%endmacro
wordvar uart_port_index, 0
wordvar uart_software_flow, 0
wordvar uart_hardware_flow, 0
wordvar uart_tx_paused, 0
bytevar uart_flow_pending, 0
bytevar uart_xoff_sent, 0
bytevar uart_rts_lowered, 0
wordvar uart_rx_write, uart_rx_buffer
wordvar uart_rx_read, uart_rx_buffer
wordvar uart_rx_last, uart_rx_buffer+4095
wordvar uart_rx_dropped, 0
wordvar uart_rx_count, 0
wordvar uart_rx_mask, 0xff
wordvar uart_port_lcr, 0x3fb
wordvar uart_port_mcr, 0x3fc
wordvar uart_port_msr, 0x3fe
wordvar uart_port_lsr, 0x3fd
wordvar uart_port_thr, 0x3f8
wordvar uart_port_ier, 0x3f9
wordvar uart_port_rbr, 0x3f8
bytevar uart_saved_pic, 0
bytevar uart_saved_lcr, 0
bytevar uart_saved_mcr, 0
bytevar uart_saved_ier, 0
bytevar uart_saved_dll, 0
bytevar uart_saved_dlm, 0
wordvar uart_irq_indices, 4
wordvar uart_irq_enable_masks, 0xff
 dw 0xff, 0xff, 0xf7, 0xef, 0xff, 0xff, 0xff
wordvar uart_irq_disable_masks, 0
 dw 0, 0, 8, 0x10, 0, 0, 0
global uart_flow_message
uart_flow_message: db 'Wait for XON', 0 ; Must fit the original14-character region.
SEGMENT _BSS public align=16 class=BSS use16
global uart_rx_buffer, uart_flow_screen_save
uart_rx_buffer: resb 4096
uart_flow_screen_save: resb 512
SEGMENT STACK stack align=16 class=STACK use16
