; Retained live IRQ owner for a DOS Gateway child. No DOS/BIOS calls or RBR
; reads in admission/return; RX dispatch executes the existing UART ISR.
BITS 16
CPU 8086
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
SEGMENT FILE_CODE public align=16 class=FARCODE use16
extern hardware_active,vector_active,terminal_program_active,terminal_program_pending,terminal_program_kind
extern terminal_irq_vector,terminal_tx_count,uart_break_hold
extern uart_port_rbr,uart_port_thr,uart_port_ier,uart_port_lcr,uart_port_mcr,uart_port_lsr
extern uart_port_index,uart_irq_indices,uart_receive_interrupt
extern uart_rx_dropped,uart_flow_pending,uart_software_flow,uart_hardware_flow,uart_rts_lowered
global gateway_uart_begin,gateway_uart_return,gateway_uart_end,gateway_uart_interrupt
global gateway_uart_storage,gateway_uart_storage_end,gateway_uart_active,gateway_uart_fault
global gateway_uart_carrier_falls,gateway_uart_dcd_delta
global gateway_uart_foreground_flow

%macro enter 0
 pushf
 push bp
 mov bp,sp
 push si
 push di
 push es
%endmacro
%macro leave 0
 pop es
 pop di
 pop si
 pop bp
 popf
 retf
%endmacro
; Context only: do not enter DOS or touch port state on an ABI refusal.
context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,DGROUP
 cmp ax,dx
 jne .bad
 test word [ss:bp+2],0x400
 jnz .bad
 mov ax,1
 ret
.bad:
 xor ax,ax
 ret

gateway_uart_begin:
 enter
 call context
 or ax,ax
 jz .bad
 test word [ss:bp+2],0x200
 jz .bad
 cli
 cmp word [cs:gateway_uart_storage],0x4755
 jne .bad
 cmp word [cs:gateway_uart_active],0
 jne .bad
 cmp word [terminal_program_active],1
 jne .bad
 cmp word [terminal_program_pending],0
 jne .bad
 cmp word [terminal_program_kind],9
 jne .bad
 cmp byte [hardware_active],1
 jne .bad
 cmp byte [vector_active],1
 jne .bad
 mov ax,[terminal_tx_count]
 or ax,[uart_break_hold]
 or al,[uart_flow_pending]
 jnz .busy
 cmp word [uart_rx_dropped],0
 jne .overrun
 mov ax,[uart_port_rbr]
 cmp ax,0x3f8
 je .base
 cmp ax,0x2f8
 je .base
 cmp ax,0x3e8
 je .base
 cmp ax,0x2e8
 jne .bad
.base:
 cmp ax,[uart_port_thr]
 jne .bad
 mov di,ax
 inc ax
 cmp ax,[uart_port_ier]
 jne .bad
 add ax,2
 cmp ax,[uart_port_lcr]
 jne .bad
 inc ax
 cmp ax,[uart_port_mcr]
 jne .bad
 inc ax
 cmp ax,[uart_port_lsr]
 jne .bad
 mov bx,[uart_port_index]
 cmp bx,3
 ja .bad
 shl bx,1
 mov cx,[uart_irq_indices+bx]
 cmp cx,3
 je .irq
 cmp cx,4
 je .irq
 cmp cx,5
 je .irq
 cmp cx,7
 jne .bad
.irq:
 mov bx,cx
 add bx,8
 cmp bx,[terminal_irq_vector]
 jne .bad
 mov ax,1
 shl ax,cl
 mov ah,al
 in al,0x21
 test al,ah
 jnz .bad
 mov [cs:irq_mask],ah
 mov [cs:port_base],di
 mov [cs:irq_vector],bx
 shl bx,1
 shl bx,1
 xor ax,ax
 mov es,ax
 cmp word [es:bx],uart_receive_interrupt
 jne .bad
 mov ax,seg uart_receive_interrupt
 cmp [es:bx+2],ax
 jne .bad
 mov [cs:parent_segment],ax
 mov word [cs:parent_offset],uart_receive_interrupt
 mov dx,di
 add dx,3
 in al,dx
 test al,0xc0
 jnz .line
 mov [cs:saved_lcr],al
 mov dx,di
 add dx,2
 in al,dx
 test al,0xc0
 jnz .line ; The parent driver has a known FIFO-disabled policy.
 mov dx,di
 inc dx
 in al,dx
 cmp al,1
 jne .line
 mov [cs:saved_ier],al
 mov dx,di
 add dx,4
 in al,dx
 test al,0x10
 jnz .line
 test al,8
 jz .line
 mov [cs:saved_mcr],al
 mov dx,di
 add dx,5
 in al,dx
 test al,2
 jnz .overrun
 and al,0x60
 cmp al,0x60
 jne .busy
 mov al,[cs:saved_lcr]
 or al,0x80
 mov dx,di
 add dx,3
 out dx,al
 mov dx,di
 in al,dx
 mov [cs:saved_dll],al
 inc dx
 in al,dx
 mov [cs:saved_dlm],al
 mov dx,di
 add dx,3
 mov al,[cs:saved_lcr]
 out dx,al
 mov word [cs:gateway_uart_fault],0
 mov byte [cs:gateway_uart_carrier_falls],0
 mov byte [cs:gateway_uart_dcd_delta],0
 mov word [cs:gateway_uart_active],1
 mov word [es:bx],gateway_uart_interrupt
 mov word [es:bx+2],cs
 mov dx,di
 inc dx
 mov al,9 ; RDA and modem-status IRQs; THRE is enabled only for queued flow.
 out dx,al
 xor ax,ax
 jmp .done
.overrun:
 mov ax,5
 jmp .done
.busy:
 mov ax,7
 jmp .done
.line:
 mov ax,8
 jmp .done
.bad:
 mov ax,4
.done:
 leave

; Called only from raw EXEC's IF0, restored DS=SS boundary. AX0 means the
; parent IRQ path is safe to enable; AX1 requests the existing quiet fallback.
gateway_uart_return:
 enter
 call context
 or ax,ax
 jz .bad
 test word [ss:bp+2],0x200
 jnz .bad
 call repair
 jmp .done
.bad:
 mov ax,1
.done:
 leave

; Repair at IF0, leaving the live wrapper installed until END. Do not replace
; native startup snapshots, reset the ring, read RBR, or restore unrelated PIC bits.
repair:
 cmp word [cs:gateway_uart_storage],0x4755
 jne .bad
 cmp word [cs:gateway_uart_active],1
 jne .bad
 mov di,[cs:port_base]
 cmp di,[uart_port_rbr]
 jne .bad
 cmp word [cs:parent_offset],uart_receive_interrupt
 jne .bad
 mov ax,seg uart_receive_interrupt
 cmp [cs:parent_segment],ax
 jne .bad
 mov cx,[cs:irq_vector]
 cmp cx,[terminal_irq_vector]
 jne .bad
 sub cx,8
 cmp cx,3
 jb .bad
 cmp cx,7
 ja .bad
 cmp cx,6
 je .bad
 mov ax,1
 shl ax,cl
 cmp al,[cs:irq_mask]
 jne .bad
 test byte [cs:saved_lcr],0xc0
 jnz .bad
 cmp byte [cs:saved_ier],1
 jne .bad
 in al,0x21
 or al,[cs:irq_mask]
 out 0x21,al
 mov dx,di
 add dx,4
 in al,dx
 xor al,[cs:saved_mcr]
 and al,0xfd ; Parent ISR owns RTS changes at its receive high watermark.
 jz .mcr
 call line_fault
.mcr:
 mov dx,di
 add dx,3
 in al,dx
 cmp al,[cs:saved_lcr]
 je .lcr
 call line_fault
.lcr:
 and al,0x3f
 out dx,al
 mov dx,di
 inc dx
 in al,dx
 and al,0xfd
 cmp al,9
 je .ier_ok
 call line_fault
.ier_ok:
 xor al,al
 out dx,al
 mov bx,[cs:irq_vector]
 shl bx,1
 shl bx,1
 xor ax,ax
 mov es,ax
 cmp word [es:bx],gateway_uart_interrupt
 jne .vector_fault
 mov ax,cs
 cmp [es:bx+2],ax
 je .vector_ok
.vector_fault:
 call line_fault
.vector_ok:
 mov word [es:bx],gateway_uart_interrupt
 mov word [es:bx+2],cs
 mov dx,di
 add dx,2
 in al,dx
 test al,0xc0
 jz .fifo
 xor al,al
 out dx,al
 call line_fault
.fifo:
 call modem_sample
 mov dx,di
 add dx,5
 in al,dx
 call errors
 test al,0x40
 jnz .tx
 cmp word [cs:gateway_uart_fault],0
 jne .tx
 mov word [cs:gateway_uart_fault],7
.tx:
 mov dx,di
 add dx,3
 mov al,[cs:saved_lcr]
 or al,0x80
 out dx,al
 mov dx,di
 in al,dx
 cmp al,[cs:saved_dll]
 je .dll
 call line_fault
.dll:
 mov al,[cs:saved_dll]
 out dx,al
 inc dx
 in al,dx
 cmp al,[cs:saved_dlm]
 je .dlm
 call line_fault
.dlm:
 mov al,[cs:saved_dlm]
 out dx,al
 mov dx,di
 add dx,3
 mov al,[cs:saved_lcr]
 out dx,al
 mov al,[cs:saved_mcr]
 cmp word [uart_hardware_flow],0
 je .rts
 cmp byte [uart_rts_lowered],0
 je .rts
 and al,0xfd
.rts:
 mov dx,di
 add dx,4
 out dx,al
 call flow
 in al,0x21
 mov ah,[cs:irq_mask]
 not ah
 and al,ah ; Entry admitted an unmasked parent IRQ. Keep other owners' bits.
 out 0x21,al
 xor ax,ax
 ret
.bad:
 mov ax,1
 ret

gateway_uart_end:
 enter
 call context
 or ax,ax
 jz .bad
 test word [ss:bp+2],0x200
 jz .bad
 cli
 call repair
 or ax,ax
 jnz .bad
 mov bx,[cs:irq_vector]
 shl bx,1
 shl bx,1
 xor ax,ax
 mov es,ax
 mov ax,[cs:parent_offset]
 mov [es:bx],ax
 mov ax,[cs:parent_segment]
 mov [es:bx+2],ax
 mov dx,[cs:port_base]
 inc dx
 mov al,[cs:saved_ier]
 out dx,al
 mov word [cs:gateway_uart_active],0
 mov ax,[cs:gateway_uart_fault]
 jmp .done
.bad:
 mov ax,4
.done:
 leave

; The wrapper owns only RDA/timeout, THRE-flow and modem status. Original RX
; code retains byte/control handling and EOI. Added work is bounded, no DOS.
gateway_uart_interrupt:
 push ax
 push dx
 push ds
 mov ax,DGROUP
 mov ds,ax
 mov dx,[cs:port_base]
 add dx,2
 in al,dx
 and al,0x0f
 cmp al,4
 je .rx
 cmp al,0x0c
 je .rx
 cmp al,2
 je .flow
 cmp al,0
 je .modem
 cmp al,6
 je .line
 jmp .eoi
.rx:
 pushf
 call far uart_receive_interrupt ; Native IRET returns to the following flow pump.
 call flow
 jmp .done
.modem:
 call modem_sample
 jmp .flow
.line:
 mov dx,[cs:port_base]
 add dx,5
 in al,dx
 call errors
.flow:
 call flow
.eoi:
 mov al,0x20
 out 0x20,al
.done:
 pop ds
 pop dx
 pop ax
 iret

; AL's LSR value survives error accounting for the caller's TEMT/THRE check.
errors:
 cmp word [uart_rx_dropped],0
 je .hardware
 mov word [cs:gateway_uart_fault],5
.hardware:
 test al,2
 jz .line
 mov word [cs:gateway_uart_fault],5
 cmp word [uart_rx_dropped],0xffff
 je .line
 inc word [uart_rx_dropped]
.line:
 test al,0x1c
 jz .done
 call line_fault
.done:
 ret
line_fault:
 cmp word [cs:gateway_uart_fault],5
 je .done
 mov word [cs:gateway_uart_fault],8
.done:
 ret
modem_sample:
 mov dx,[cs:port_base]
 add dx,6
 in al,dx
 test al,8
 jz .done
 mov byte [cs:gateway_uart_dcd_delta],1
 test al,0x80
 jnz .done
 mov byte [cs:gateway_uart_carrier_falls],1
.done:
 ret
flow:
 cmp word [uart_hardware_flow],0
 je .lsr
 extern uart_rx_count
 cmp word [uart_rx_count],3072
 jb .lsr
 mov dx,[cs:port_base]
 add dx,4
 in al,dx
 and al,0xfd
 out dx,al
 mov byte [uart_rts_lowered],1
.lsr:
 mov dx,[cs:port_base]
 add dx,5
 in al,dx
 call errors
 mov ah,9
 cmp word [uart_software_flow],0
 je .ier
 cmp byte [uart_flow_pending],0
 je .ier
 cmp byte [uart_flow_pending],0x11
 je .valid
 cmp byte [uart_flow_pending],0x13
 jne .invalid
.valid:
 test al,0x20
 jz .later
 mov al,[uart_flow_pending]
 mov dx,[cs:port_base]
 out dx,al
 mov byte [uart_flow_pending],0
 jmp .ier
.later:
 or ah,2
 jmp .ier
.invalid:
 call line_fault
.ier:
 mov dx,[cs:port_base]
 inc dx
 mov al,ah
 out dx,al
 ret

; Poll's IF0 foreground bracket completes combined S/H low-water recovery.
; Native software dequeue retires XOFF before reaching its hardware branch.
; Preserve current DTR/OUT2 and release only the driver's marked RTS hold.
gateway_uart_foreground_flow:
 cmp word [cs:gateway_uart_active],0
 jne .done
 cmp word [uart_hardware_flow],0
 je .done
 cmp byte [uart_rts_lowered],0
 je .done
 cmp word [uart_rx_count],128
 ja .done
 mov dx,[uart_port_mcr]
 in al,dx
 or al,2
 out dx,al
 mov byte [uart_rts_lowered],0
.done:
 retf

align 2
gateway_uart_storage: dw 0x4755
gateway_uart_active: dw 0
gateway_uart_fault: dw 0
port_base: dw 0
irq_vector: dw 0
parent_offset: dw 0
parent_segment: dw 0
irq_mask: db 0
saved_lcr: db 0
saved_ier: db 0
saved_mcr: db 0
saved_dll: db 0
saved_dlm: db 0
gateway_uart_carrier_falls: db 0
gateway_uart_dcd_delta: db 0
gateway_uart_storage_end:
%if gateway_uart_storage_end-gateway_uart_storage!=22
 %error Gateway UART storage layout changed
%endif
