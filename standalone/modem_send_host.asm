; Source-only actual sender diagnostic. Real recovered UART, fixed COM1/38400/8N1.
; Original blocking sender receives a compile-time valid synthetic command only.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern modem_send_original,uart_save_hardware_state,uart_restore_hardware_state
extern uart_disable,uart_set_baud_divisor,uart_set_line_control,uart_wait_transmitter_empty
extern stack_top
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 call uart_save_hardware_state
 call uart_disable
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
 ; Poll TX only; no receive interrupt is installed or enabled.
 mov dx,0x3f9
 xor al,al
 out dx,al
 mov dx,0x3fc
 mov al,3
 out dx,al
 mov ax,modem_send_command
 push ax
 call modem_send_original
 pop bx
 call uart_wait_transmitter_empty
 call uart_restore_hardware_state
 mov ax,0x4c00
 int 0x21
; Maintained diagnostic BIOS echo, not the original0610 terminal renderer.
global modem_send_echo_character
modem_send_echo_character:
 push bp
 mov bp,sp
 push bx
 mov ax,[bp+4]
 mov ah,0x0e
 xor bx,bx
 int 0x10
 pop bx
 pop bp
 ret
; Explicit unsupported presentation boundaries of the recovered UART driver.
; Default fixed NO FLOW never calls these; they are not fake UART services.
global pcplus_flow_message,pcplus_screen_save,pcplus_screen_restore
pcplus_flow_message:
pcplus_screen_save:
pcplus_screen_restore:
 int 3
 ret
; Real diagnostic BIOS bell, DOS seconds and keyboard Escape detection.
global pcplus_flow_bell,pcplus_seconds,pcplus_escape_pressed
pcplus_flow_bell:
 push ax
 push bx
 mov ax,0x0e07
 xor bx,bx
 int 0x10
 pop bx
 pop ax
 ret
pcplus_seconds:
 push cx
 push dx
 mov ah,0x2c
 int 0x21
 xor ax,ax
 mov al,dh
 pop dx
 pop cx
 ret
pcplus_escape_pressed:
 mov ah,1
 int 0x16
 jz .no
 cmp al,27
 jne .no
 mov ah,0
 int 0x16
 mov ax,1
 ret
.no:
 xor ax,ax
 ret
SEGMENT _DATA public align=16 class=DATA use16
global modem_send_pause_marker,modem_send_local_echo,modem_send_pacing_units
global modem_send_delay_floor,modem_send_delay_count,modem_send_command
modem_send_pause_marker: db '~'
modem_send_local_echo: dw 1
modem_send_pacing_units: dw 2
; Explicit fixture calibration, not recovered physical-time calibration.
modem_send_delay_floor: dw 0
modem_send_delay_count: dw 1
modem_send_command: db 'AT~X^@^M^^^',0
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
