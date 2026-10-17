; Source-only DOS UART diagnostic using the recovered PCPlus serial module.
; COM1, IRQ4, 38400 8N1; echoes binary input. Escape on the local keyboard exits.
; Command tail S enables XON/XOFF; H enables RTS/CTS; default disables flow control.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern uart_save_hardware_state, uart_restore_hardware_state
extern uart_install_interrupt, uart_restore_interrupt, uart_disable, uart_enable
extern uart_clear_receive_buffer, uart_set_baud_divisor, uart_set_line_control
extern uart_receive_byte, uart_transmit_byte, uart_transmit_cl
extern uart_software_flow, uart_hardware_flow, stack_top
extern uart_rx_write, uart_rx_read, uart_rx_count, uart_rx_buffer
extern uart_tx_paused, uart_xoff_sent, uart_rts_lowered
..start:
 mov ax,DGROUP
 mov ds,ax
 ; Recovered routines address stack arguments through DS:BX, requiring SS=DS.
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 ; On DOS entry ES identifies the PSP. Read the first command-tail character.
 xor bx,bx
 mov bl,[es:0x80]
 mov si,0x81
.arg:
 or bx,bx
 jz .configure
 mov al,[es:si]
 inc si
 dec bx
 cmp al,' '
 je .arg
 and al,0xdf
 cmp al,'S'
 jne .hardware
 mov word [uart_software_flow],1
 jmp .configure
.hardware:
 cmp al,'H'
 jne .configure
 mov word [uart_hardware_flow],1
.configure:
 ; Save the vector separately, and remember the program's initial vector.
 mov ax,0x350c
 int 0x21
 mov [previous_offset],bx
 mov [previous_segment],es
 call uart_save_hardware_state
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_install_interrupt
 add sp,2
 call uart_clear_receive_buffer
 xor ax,ax
 push ax
 mov ax,38400
 push ax
 call uart_set_baud_divisor
 add sp,4
 mov ax,1
 push ax
 mov ax,8
 push ax
 xor ax,ax
 push ax
 call uart_set_line_control
 add sp,6
 call uart_enable
 mov si,ready
 call send_string
.loop:
 mov ah,1
 int 0x16
 jz .receive
 mov ah,0
 int 0x16
 cmp al,27
 je .exit
.receive:
 call uart_receive_byte
 cmp ax,0xffff
 je .loop
 push ax
 call uart_transmit_byte
 jmp .loop
.exit:
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_restore_interrupt
 add sp,2
 call uart_restore_hardware_state
 ; Verify restored interrupt vector and internal ring invariants in DOS.
 mov ax,0x350c
 int 0x21
 cmp bx,[previous_offset]
 jne .failed
 mov ax,es
 cmp ax,[previous_segment]
 jne .failed
 cmp word [uart_rx_count],0
 jne .failed
 mov ax,[uart_rx_read]
 cmp ax,[uart_rx_write]
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
send_string:
 lodsb
 or al,al
 jz .done
 mov cl,al
 call uart_transmit_cl
 jmp send_string
.done:
 ret
SEGMENT _DATA public class=DATA use16
previous_offset: dw 0
previous_segment: dw 0
ready: db 'LOC-UART-READY',13,0
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
