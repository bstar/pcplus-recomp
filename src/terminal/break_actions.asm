; Maintained serviced serial BREAK owner; native evidence: docs/BREAK_NATIVE.md.
; DS=SS, foreground only. All public entries preserve registers and FLAGS.
; State0 idle,1 draining TEMT,2 electrically asserted. No fake THR byte.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern hardware_active,vector_active,terminal_quit,connection_state
extern terminal_macro_active,terminal_program_pending,terminal_program_active
extern terminal_transfer_pending,terminal_transfer_active,terminal_ansi_wait_active
extern terminal_controller_active,uart_port_lcr,uart_port_lsr,uart_break_hold
extern terminal_clock_ticks
global terminal_break_start,terminal_break_poll,terminal_break_cancel

%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push bp
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop bp
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
%endmacro
terminal_break_start:
 extern terminal_recording_owned_far
 save
 call far terminal_recording_owned_far
 or ax,ax
 jnz .done
 mov word [terminal_break_status],2
 cmp word [terminal_break_state],0
 jne .done
 cmp word [terminal_quit],0
 jne .done
 cmp word [terminal_macro_active],0
 jne .done
 cmp word [terminal_program_pending],0
 jne .done
 cmp word [terminal_program_active],0
 jne .done
 cmp word [terminal_transfer_pending],0
 jne .done
 cmp word [terminal_transfer_active],0
 jne .done
 cmp word [terminal_ansi_wait_active],0
 jne .done
 cmp word [terminal_controller_active],1
 ja .done
 cmp word [connection_state],0
 je .hardware
 cmp word [connection_state],6
 jne .done
.hardware:
 mov word [terminal_break_status],4
 cmp byte [hardware_active],1
 jne .done
 cmp byte [vector_active],1
 jne .done
 mov dx,[uart_port_lcr]
 in al,dx
 test al,0xc0 ; Neither foreign BREAK nor DLAB may be inherited.
 jnz .foreign
 mov [break_line],al
 mov ax,[connection_state]
 mov [break_connection],ax
 ; Derived nominal units are one55th BIOS tick. Round up, plus one edge
 ; for arbitrary phase. Zero retains native immediate assert/clear behavior.
 mov ax,[terminal_break_delay_units]
 xor dx,dx
 mov bx,55
 div bx
 or dx,dx
 jz .rounded
 inc ax
.rounded:
 inc ax
 mov [break_duration],ax
 call terminal_clock_ticks
 mov [break_started],ax
 mov [break_started+2],dx
 mov word [uart_break_hold],1
 mov word [terminal_break_state],1
 mov word [terminal_break_status],1
 call break_service
 jmp .done
.foreign:
 mov word [terminal_break_status],3
.done:
 restore
terminal_break_poll:
 save
 call break_service
 restore

break_service:
 cmp word [terminal_break_state],0
 je .done
 cmp byte [hardware_active],1
 jne .lost
 cmp byte [vector_active],1
 jne .lost
 cmp word [terminal_quit],0
 jne .cancel
 mov ax,[connection_state]
 cmp ax,[break_connection]
 jne .cancel
 mov dx,[uart_port_lcr]
 in al,dx
 mov ah,al
 and al,0xbf
 cmp al,[break_line]
 jne .changed
 cmp word [terminal_break_state],2
 je .asserted
 test ah,0x40 ; A foreign owner asserted while we waited: never clear it.
 jnz .foreign
 mov dx,[uart_port_lsr]
 in al,dx
 test al,0x40 ; TEMT, not merely THRE: protect the last queued stop bit.
 jnz .assert
 call break_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,19 ; At least18 complete tick intervals to finish in-flight TX.
 jb .done
.timeout:
 mov word [terminal_break_status],5
 jmp break_release
.assert:
 mov dx,[uart_port_lcr]
 mov al,[break_line]
 or al,0x40
 out dx,al
 mov word [terminal_break_state],2
 call terminal_clock_ticks
 mov [break_started],ax
 mov [break_started+2],dx
 cmp word [break_duration],1
 jne .done
 jmp .complete
.asserted:
 test ah,0x40
 jz .changed
 call break_elapsed
 or dx,dx
 jnz .complete
 cmp ax,[break_duration]
 jb .done
.complete:
 mov word [terminal_break_status],6
 jmp break_release
.changed:
 mov word [terminal_break_status],8
 jmp break_release
.foreign:
 mov word [terminal_break_status],3
 jmp break_release
.cancel:
 mov word [terminal_break_status],7
 jmp break_release
.lost:
 ; Defensive ownership-loss boundary: cannot write a UART we no longer own.
 ; Normal release paths call cancel BEFORE releasing hardware/vector ownership.
 mov word [terminal_break_status],4
 mov word [terminal_break_state],0
 mov word [uart_break_hold],0
.done:
 ret

terminal_break_cancel:
 save
 cmp word [terminal_break_state],0
 je .done
 mov word [terminal_break_status],7
 call break_release
.done:
 restore
break_release:
 cmp word [terminal_break_state],2
 jne .clear
 cmp byte [hardware_active],1
 jne .clear
 cmp byte [vector_active],1
 jne .clear
 mov dx,[uart_port_lcr]
 in al,dx
 and al,0xbf ; Release only our BREAK; preserve the current framing/DLAB bits.
 out dx,al
.clear:
 mov word [terminal_break_state],0
 mov word [uart_break_hold],0
 ret
break_elapsed:
 call terminal_clock_ticks
 sub ax,[break_started]
 sbb dx,[break_started+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done:
 ret

SEGMENT _DATA public class=DATA use16
global terminal_break_state,terminal_break_status,terminal_break_delay_units
terminal_break_state: dw 0
terminal_break_status: dw 0
terminal_break_delay_units: dw 350
break_duration: dw 0
break_started: dd 0
break_connection: dw 0
break_line: db 0
