; Fixed addresses for exact rebuilding; linker symbols for independent OMF builds.
%ifdef UART_OMF
extern uart_port_index
extern uart_software_flow
extern uart_hardware_flow
extern uart_tx_paused
extern uart_xoff_sent
extern uart_rts_lowered
extern uart_rx_write
extern uart_rx_read
extern uart_rx_last
extern uart_rx_buffer
extern uart_rx_count
extern uart_rx_mask
extern uart_port_lcr
extern uart_port_mcr
extern uart_port_msr
extern uart_port_lsr
extern uart_port_thr
extern uart_port_ier
extern uart_port_rbr
extern uart_saved_pic
extern uart_saved_lcr
extern uart_saved_mcr
extern uart_saved_ier
extern uart_saved_dll
extern uart_saved_dlm
extern uart_irq_indices
extern uart_irq_enable_masks
extern uart_irq_disable_masks
extern uart_flow_screen_save
extern uart_flow_message
extern pcplus_seconds
extern pcplus_flow_bell
extern pcplus_flow_message
extern pcplus_escape_pressed
extern pcplus_screen_restore
extern pcplus_screen_save
%else
%define uart_port_index 0x1b84
%define uart_software_flow 0x3354
%define uart_hardware_flow 0x3356
%define uart_tx_paused 0x39a6
%define uart_xoff_sent 0x7e17
%define uart_rts_lowered 0x7e18
%define uart_rx_write 0x7e19
%define uart_rx_read 0x7e1b
%define uart_rx_last 0x7e1d
%define uart_rx_buffer 0x7e20
%define uart_rx_count 0x8e20
%define uart_rx_mask 0x8e22
%define uart_port_lcr 0x8fee
%define uart_port_mcr 0x8ff4
%define uart_port_msr 0x8ffe
%define uart_port_lsr 0x900a
%define uart_port_thr 0x9012
%define uart_port_ier 0x901a
%define uart_port_rbr 0x9022
%define uart_saved_pic 0x9024
%define uart_saved_lcr 0x902c
%define uart_saved_mcr 0x9034
%define uart_saved_ier 0x9040
%define uart_saved_dll 0x9044
%define uart_saved_dlm 0x904b
%define uart_irq_indices 0x1d08
%define uart_irq_enable_masks 0x3358
%define uart_irq_disable_masks 0x3368
%define uart_flow_screen_save 0x7df9
%define uart_flow_message 0x7deb
%define pcplus_seconds 0x3323
%define pcplus_flow_bell 0x3778
%define pcplus_flow_message 0x31bb
%define pcplus_escape_pressed 0x3f4b
%define pcplus_screen_restore 0x7682
%define pcplus_screen_save 0x765c
%endif
