; Maintained synchronous external-child UART owner. No queue reset/RBR reads.
BITS 16
CPU 8086
%ifndef ASPECT_EXTERNAL_PROCESS
%error ASPECT_EXTERNAL_PROCESS guards are required in every serial object
%endif
SEGMENT _TEXT public class=CODE use16
extern _aspect_serial_active,_aspect_serial_status,serial_compile_held,serial_vector
extern serial_process_guard_level
extern uart_break_hold,uart_flow_pending,uart_port_lcr,uart_port_ier
extern uart_port_thr,uart_port_mcr,uart_port_lsr,uart_port_rbr
extern uart_rx_dropped,uart_port_index,uart_irq_indices,uart_irq_disable_masks
extern uart_mask_irq,uart_restore_interrupt,uart_receive_interrupt
global _aspect_process_serial_detach,_aspect_process_serial_restore
global _aspect_process_serial_clock_ready
_aspect_process_serial_clock_ready:
 pushf
 pushf
 pop ax
 test ax,0x200
 jz .bad
 in al,0x21
 test al,1
 jnz .bad
 xor ax,ax
 popf
 ret
.bad:
 mov ax,4
 popf
 ret

_aspect_process_serial_detach:
 pushf
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,4
 test word [ss:bp+2],0x200
 jz .done
 cli
 cmp word [serial_process_guard_level],1
 jne .done
 cmp word [_aspect_serial_active],1
 jne .done
 cmp word [serial_compile_held],1
 jne .done
 cmp word [uart_break_hold],0
 jne .done
 mov ax,[_aspect_serial_status]
 or ax,ax
 jnz .done
 mov ax,7
 cmp byte [uart_flow_pending],0
 jne .done
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jnz .overflow
 test al,0x40
 mov ax,7
 jz .done
 mov dx,[uart_port_lcr]
 in al,dx
 test al,0xc0
 jnz .line
 mov [process_lcr],al
 mov dx,[uart_port_rbr]
 add dx,2
 in al,dx
 test al,0xc0 ;FCR is write-only: admit the driver's known FIFO-disabled state.
 jnz .line
 mov ax,[serial_vector]
 mov ah,0x35
 int 0x21
 cmp bx,uart_receive_interrupt
 jne .state
 mov ax,es
 mov dx,seg uart_receive_interrupt
 cmp ax,dx
 jne .state
 mov [process_vector_offset],bx
 mov [process_vector_segment],ax
 mov dx,[uart_port_mcr]
 in al,dx
 mov [process_mcr],al
 mov al,[process_lcr]
 or al,0x80
 mov dx,[uart_port_lcr]
 out dx,al
 mov dx,[uart_port_thr]
 in al,dx
 mov [process_dll],al
 inc dx
 in al,dx
 mov [process_dlm],al
 mov al,[process_lcr]
 mov dx,[uart_port_lcr]
 out dx,al
 mov dx,[uart_port_ier]
 in al,dx
 mov [process_ier],al
 mov bx,[uart_port_index]
 shl bx,1
 mov bx,[uart_irq_indices+bx]
 shl bx,1
 mov ax,[uart_irq_disable_masks+bx]
 mov [process_irq_mask],al
 in al,0x21
 and al,[process_irq_mask]
 mov [process_pic_bit],al
 mov al,[process_mcr]
 and al,0xfd
 mov dx,[uart_port_mcr]
 out dx,al
 call uart_mask_irq
 mov dx,[uart_port_ier]
 xor al,al
 out dx,al
 push word [serial_vector]
 call uart_restore_interrupt
 add sp,2
 mov word [process_fault],0
 mov word [_aspect_process_serial_detached],1
 mov word [_aspect_serial_active],2
 xor ax,ax
 jmp .done
.overflow:
 call process_overflow
 mov word [_aspect_serial_status],5
 mov ax,5
 jmp .done
.line: mov ax,8
 jmp .done
.state: mov ax,4
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 popf
 ret

_aspect_process_serial_restore:
 pushf
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 xor ax,ax
 cmp word [_aspect_process_serial_detached],0
 je .done
 mov ax,4
 test word [ss:bp+2],0x200
 jz .done
 cli
 cmp word [_aspect_serial_active],2
 jne .done
 ; Quiet the child's hardware and retire its vector before polling or drawing.
 mov dx,[uart_port_mcr]
 in al,dx
 mov ah,al
 xor ah,[process_mcr]
 test ah,1
 jz .dtr_ok
 cmp word [process_fault],5
 je .dtr_ok
 mov word [process_fault],8
.dtr_ok:
 and al,0xfd
 out dx,al
 call uart_mask_irq
 mov dx,[uart_port_lcr]
 in al,dx
 and al,0x3f ;Clear child DLAB/BREAK before accessing IER.
 out dx,al
 mov dx,[uart_port_ier]
 xor al,al
 out dx,al
 push word [serial_vector]
 call uart_restore_interrupt
 add sp,2
 mov dx,[uart_port_rbr]
 add dx,2
 in al,dx
 test al,0xc0
 jz .fifo_ok
 xor al,al
 out dx,al ;Restore known FIFO-disabled policy; flag the unsupported child state.
 cmp word [process_fault],5
 je .fifo_ok
 mov word [process_fault],8
.fifo_ok:
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jz .overrun_ok
 call process_overflow
.overrun_ok:
 test al,0x40
 jnz .ready
 cmp word [bp+6],0 ;pushf precedes the BP frame; force is beyond FLAGS/return.
 jne .forced
 mov ax,7
 jmp .done
.forced:
 cmp word [process_fault],0
 jne .ready
 mov word [process_fault],7
.ready:
 mov al,[process_lcr]
 or al,0x80
 mov dx,[uart_port_lcr]
 out dx,al
 mov dx,[uart_port_thr]
 mov al,[process_dll]
 out dx,al
 inc dx
 mov al,[process_dlm]
 out dx,al
 mov dx,[uart_port_lcr]
 mov al,[process_lcr]
 out dx,al
 ; Install the saved parent vector directly. Reinstalling through native AD65
 ; here would overwrite the shutdown baseline with the child's vector.
 mov ax,[serial_vector]
 mov ah,0x25
 mov dx,[process_vector_offset]
 mov bx,[process_vector_segment]
 push ds
 mov ds,bx
 int 0x21
 pop ds
 mov word [_aspect_serial_active],1
 mov word [_aspect_process_serial_detached],0
 mov dx,[uart_port_mcr]
 mov al,[process_mcr]
 out dx,al
 mov dx,[uart_port_ier]
 mov al,[process_ier]
 out dx,al
 in al,0x21
 mov ah,[process_irq_mask]
 not ah
 and al,ah
 or al,[process_pic_bit]
 out 0x21,al ;Other PIC bits belong to other owners and keep their current values.
 mov ax,[process_fault]
 cmp word [_aspect_serial_status],0
 jne .status
 mov [_aspect_serial_status],ax
.status:
 mov ax,[_aspect_serial_status]
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 popf
 ret
process_overflow:
 mov word [process_fault],5
 cmp word [uart_rx_dropped],0xffff
 je .done
 inc word [uart_rx_dropped]
.done: ret
; Local state needs group fixups too: C CONST precedes _DATA in this host.
GROUP DGROUP _DATA _BSS STACK
SEGMENT _DATA public class=DATA use16
global _aspect_process_serial_detached
_aspect_process_serial_detached: dw 0
process_vector_offset: dw 0
process_vector_segment: dw 0
process_fault: dw 0
process_lcr: db 0
process_dll: db 0
process_dlm: db 0
process_ier: db 0
process_mcr: db 0
process_irq_mask: db 0
process_pic_bit: db 0
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
