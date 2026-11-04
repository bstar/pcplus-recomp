; Diagnostic foreground calls only; separate from application command bindings.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_poll_io,terminal_tick_low,csi_reset_terminal,uart_receive_byte
extern terminal_redisplay_before,terminal_connection_receive,terminal_monitor_filter
extern terminal_controller_filter,terminal_transfer_filter,_terminal_autostart_input
global status_probe_poll,status_probe_ticks,status_probe_ris
status_probe_poll:
 push bp
 push bx
 push si
 push di
 push es
 push ds
 pop es
 call terminal_poll_io
 ; Main's receive sequence is inline. Use the same genuine receiver/filter/
 ; autodetect services here; escape continuations read the real UART ring.
 call uart_receive_byte
 cmp ax,0xffff
 je .done
 call terminal_redisplay_before
 call terminal_connection_receive
 jc .done
 call terminal_monitor_filter
 jc .done
 call terminal_controller_filter
 jc .done
 call terminal_transfer_filter
 jc .done
 push ax
 call _terminal_autostart_input
 add sp,2
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 retf
status_probe_ticks:
 call terminal_tick_low
 retf
status_probe_ris:
 call csi_reset_terminal
 retf

SEGMENT CONFIG_CODE public class=FARCODE use16
; Far cdecl(name near,buffer far,count). Exclusive DOS creation; one close per
; acquired handle. Never overwrite an existing diagnostic or private file.
global status_probe_write
status_probe_write:
 push bp
 mov bp,sp
 sub sp,2
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov word [bp-2],1
 mov dx,[bp+6]
 xor cx,cx
 mov ax,0x5b00
 int 0x21
 jc .done
 mov bx,ax
 mov word [bp-2],2
 push ds
 mov ds,[bp+10]
 mov dx,[bp+8]
 mov cx,[bp+12]
 mov ah,0x40
 int 0x21
 pop ds
 jc .close
 cmp ax,[bp+12]
 jne .close
 mov word [bp-2],0
.close:
 mov ah,0x3e
 int 0x21
 jnc .done
 cmp word [bp-2],0
 jne .done
 mov word [bp-2],3
.done:
 mov ax,[bp-2]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf
