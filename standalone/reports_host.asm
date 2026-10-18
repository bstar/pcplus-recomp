; Isolated output capture for source-built reports; no screen/UART emulation.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern csi_device_status
global csi_transmit_byte,csi_transmit_string
csi_transmit_byte:
 mov bx,sp
 mov ax,[bx+2]
 mov bx,[reports_output_length]
 mov [reports_output_buffer+bx],al
 inc word [reports_output_length]
 ret 2
csi_transmit_string:
 push bp
 mov bp,sp
 push si
 mov si,[bp+4]
.loop:
 lodsb
 or al,al
 jz .done
 xor ah,ah
 push ax
 call csi_transmit_byte
 jmp .loop
.done:
 pop si
 pop bp
 ret 2
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 call csi_device_status
 cmp word [reports_output_length],4
 jne .failed
 cmp word [reports_output_buffer],0x5b1b
 jne .failed
 cmp word [reports_output_buffer+2],0x6e30
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
%macro wordvar 2
 global %1
 %1: dw %2
%endmacro
wordvar ansi_parameters,5
wordvar ansi_private,0
wordvar screen_cursor_row,9
wordvar screen_cursor_column,19
wordvar csi_origin_row,0
wordvar csi_report_private_prefix,0
wordvar csi_printer_ready,0
wordvar csi_terminal_id,2
wordvar reports_output_length,0
global reports_output_buffer,reports_decimal_test_buffer
reports_output_buffer: times 512 db 0
reports_decimal_test_buffer: times 7 db 0
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
