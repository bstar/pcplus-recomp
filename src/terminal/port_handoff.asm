; Maintained foreground single-UART ownership transfer. No original driver
; bytes are changed. The settings UI does not invoke this entry yet.
BITS 16
CPU 8086
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_program_active,terminal_program_kind,terminal_program_status
extern terminal_program_mcr,terminal_port_number,terminal_irq_vector
extern connection_state,terminal_tx_count
extern uart_port_index,uart_irq_indices
extern uart_irq_disable_masks
extern uart_port_rbr,uart_port_thr,uart_port_ier,uart_port_lcr
extern uart_port_mcr,uart_port_lsr,uart_port_msr
extern uart_rx_count,uart_rx_dropped,uart_tx_paused
extern uart_xoff_sent,uart_flow_pending,uart_rts_lowered
extern uart_restore_interrupt,uart_restore_hardware_state
extern uart_save_hardware_state,uart_disable,uart_install_interrupt
global terminal_port_handoff

; AX validated TI_SIZE-byte candidate in DS. Foreground setup owner only:
; child has returned, its ISR was removed, old-format XON/TEMT handoff completed.
; AX0 acquired target,1 invalid candidate/owner,2 occupied/not drained.
; Preserve BP/SI/DI/ES. Failures precede any resource transfer. On success the
; target is IRQ-masked, IER0, DLAB0 with its original vector installed; the normal
; PROGRAM restore must install the desired serial format and re-enable it.
; All earlier ports are already restored, so one native snapshot is sufficient.
terminal_port_handoff:
 push bp
 push si
 push di
 push es
 mov si,ax
 or ax,ax
 jz .invalid
 add ax,TI_SIZE-1
 jc .invalid
 cmp word [terminal_program_active],1
 jne .invalid
 cmp word [terminal_program_kind],1
 jne .invalid
 cmp word [terminal_program_status],4
 jne .invalid
 mov bx,[si+TI_PORT]
 dec bx
 cmp bx,3
 ja .invalid
 shl bx,1
 mov dx,[cs:port_bases+bx]
 cmp dx,[si+TI_IO_BASE]
 jne .invalid
 mov ax,[cs:port_irqs+bx]
 cmp ax,[si+TI_IRQ]
 jne .invalid
 cmp dx,[uart_port_rbr]
 je .invalid ;Never capture the live UART as its own startup baseline.
 mov ax,0x40
 mov es,ax
 cmp dx,[es:bx]
 jne .invalid ;Do not probe ports absent from the BIOS table.
 cmp word [connection_state],0
 jne .busy
 cmp word [terminal_tx_count],0
 jne .busy
 cmp word [uart_rx_count],0
 jne .busy
 cmp byte [uart_xoff_sent],0
 jne .busy
 cmp byte [uart_flow_pending],0
 jne .busy
 mov bx,[uart_irq_indices]
 shl bx,1
 in al,0x21
 test al,[uart_irq_disable_masks+bx]
 jz .busy
 mov dx,[uart_port_lcr]
 in al,dx
 test al,0x80
 jnz .busy
 mov dx,[uart_port_ier]
 in al,dx
 or al,al
 jnz .busy
 mov dx,[uart_port_mcr]
 in al,dx
 test al,2
 jnz .busy
 ; LSR reads acknowledge overrun. Retain that loss even on a rejected request.
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jz .old_lsr
 cmp word [uart_rx_dropped],0xffff
 je .busy
 inc word [uart_rx_dropped]
 jmp .busy
.old_lsr:
 and al,0x61
 cmp al,0x60
 jne .busy
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x80
 jnz .busy
 mov dx,[si+TI_IO_BASE]
 add dx,5
 in al,dx
 test al,2
 jz .target_lsr
 cmp word [uart_rx_dropped],0xffff
 je .busy
 inc word [uart_rx_dropped]
 jmp .busy
.target_lsr:
 and al,0x63
 cmp al,0x60
 jne .busy ;No target RBR read or data discard, including pending overrun.
 inc dx
 in al,dx
 test al,0x80
 jnz .busy
 ; The old vector belongs to the old IRQ until restoration is complete.
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
 call uart_restore_hardware_state
 mov ax,[si+TI_PORT]
 mov [terminal_port_number],ax
 mov ax,[si+TI_IRQ]
 mov [uart_irq_indices],ax
 add ax,8
 mov [terminal_irq_vector],ax
 mov word [uart_port_index],0
 mov dx,[si+TI_IO_BASE]
 mov [uart_port_rbr],dx
 mov [uart_port_thr],dx
 inc dx
 mov [uart_port_ier],dx
 add dx,2
 mov [uart_port_lcr],dx
 inc dx
 mov [uart_port_mcr],dx
 inc dx
 mov [uart_port_lsr],dx
 inc dx
 mov [uart_port_msr],dx
 call uart_save_hardware_state
 call uart_disable ;Snapshot leaves DLAB1; disable clears it before IER0.
 ; Seed the native saved vector from the TARGET IRQ. The old saved vector must
 ; never be restored into this slot by PROGRAM's later restoration routine.
 push word [terminal_irq_vector]
 call uart_install_interrupt
 add sp,2
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
 mov byte [terminal_program_mcr],0x0b
 mov word [uart_tx_paused],0
 mov byte [uart_xoff_sent],0
 mov byte [uart_flow_pending],0
 mov byte [uart_rts_lowered],0
 xor ax,ax
 jmp .done
.invalid:
 mov ax,1
 jmp .done
.busy:
 mov ax,2
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
port_bases: dw 0x3f8,0x2f8,0x3e8,0x2e8
port_irqs: dw 4,3,4,3
