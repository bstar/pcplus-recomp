; Explicit maintained child UART owner. Links actual recovered UART core/ISR
; and maintained bounded UART API. No native blocking transmit/UI path is used.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_save_hardware_state,uart_restore_hardware_state
extern uart_install_interrupt,uart_restore_interrupt,uart_receive_byte
extern uart_try_write,uart_poll_flow,uart_mask_irq
extern uart_saved_ds,uart_previous_irq_offset,uart_previous_irq_segment
extern uart_break_hold
extern _aspect_serial_preload
global _aspect_serial_backend_open,_aspect_serial_backend_close
 global _aspect_serial_available,_aspect_serial_read,_aspect_serial_try_write
 global _aspect_serial_unread
 global _aspect_serial_poll,_aspect_serial_ticks
_aspect_serial_backend_open:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 cmp word [_aspect_serial_active],0
 jne .busy
 mov word [serial_unread_valid],0
 mov ax,[bp+4]
 cmp ax,3
 ja .arg
 mov bx,ax
 shl bx,1
 push ds
 mov ax,0x40
 mov es,ax
 mov ax,[es:bx]
 pop ds
 cmp ax,[serial_bases+bx]
 jne .absent
 mov [uart_port_index],bx ;temporary; real index restored below.
 mov [uart_port_rbr],ax
 mov [uart_port_thr],ax
 inc ax
 mov [uart_port_ier],ax
 add ax,2
 mov [uart_port_lcr],ax
 inc ax
 mov [uart_port_mcr],ax
 inc ax
 mov [uart_port_lsr],ax
 inc ax
 mov [uart_port_msr],ax
 mov ax,[bp+4]
 mov [uart_port_index],ax
 mov bx,ax
 shl bx,1
 mov ax,[serial_vectors+bx]
 mov [serial_vector],ax
 ; Establish complete baseline before enabling any child interrupt. Preserve
 ; DTR exactly: this explicit lease requires an already asserted connection.
 call uart_save_hardware_state
 test byte [uart_saved_mcr],1
 jz .restore_reject
 mov al,[uart_saved_lcr]
 and al,0x7f
 mov dx,[uart_port_lcr]
 out dx,al
 mov dx,[uart_port_ier]
 xor al,al
 out dx,al
 call uart_mask_irq
 mov word [uart_rx_count],0
 mov word [uart_rx_dropped],0
 mov word [uart_rx_mask],255
 mov word [uart_rx_read],uart_rx_buffer
 mov word [uart_rx_write],uart_rx_buffer
 mov word [uart_tx_paused],0
 mov word [uart_software_flow],0
 mov word [uart_hardware_flow],0
 mov byte [uart_flow_pending],0
 mov byte [uart_xoff_sent],0
 mov byte [uart_rts_lowered],0
 mov word [uart_break_hold],0
 cmp word [bp+10],'B'
 je .soft
 cmp word [bp+10],'S'
 jne .hard
.soft:
 mov word [uart_software_flow],1
 mov byte [uart_flow_pending],0x11 ;release parent pause, foreground sends.
.hard:
 cmp word [bp+10],'B'
 je .both
 cmp word [bp+10],'H'
 jne .format
.both:
 mov word [uart_hardware_flow],1
.format:
 call _aspect_serial_preload
 cmp word [uart_rx_count],3072
 jb .preload_ready
 cmp word [uart_software_flow],0
 je .preload_hard
 mov byte [uart_xoff_sent],1
 mov byte [uart_flow_pending],0x13
.preload_hard:
 cmp word [uart_hardware_flow],0
 je .preload_ready
 mov byte [uart_rts_lowered],1
.preload_ready:
 mov dx,[uart_port_lcr]
 mov al,0x80
 out dx,al
 mov ax,[bp+6]
 mov dx,[uart_port_thr]
 out dx,al
 inc dx
 mov al,ah
 out dx,al
 mov dx,[uart_port_lcr]
 mov ax,[bp+8]
 out dx,al
 push word [serial_vector]
 call uart_install_interrupt
 add sp,2
 mov word [_aspect_serial_status],0
 mov word [_aspect_serial_active],1
 mov dx,[uart_port_mcr]
 mov al,[uart_saved_mcr]
 or al,0x0a ;RTS+OUT2; DTR untouched, already1.
 cmp byte [uart_rts_lowered],0
 je .mcr_ready
 and al,0xfd
.mcr_ready:
 out dx,al
 mov dx,[uart_port_ier]
 mov al,1
 out dx,al
 mov bx,[uart_port_index]
 shl bx,1
 mov bx,[uart_irq_indices+bx]
 shl bx,1
 mov ah,[uart_irq_disable_masks+bx]
 not ah
 in al,0x21
 and al,ah
 out 0x21,al
 ; Never call uart_enable: it discards pending RBR.
 xor ax,ax
 jmp .done
.restore_reject:
 call uart_restore_hardware_state
 mov ax,4
 jmp .done
.busy: mov ax,2
 jmp .done
.absent: mov ax,3
 jmp .done
.arg: mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_aspect_serial_available:
 xor ax,ax
 cmp word [_aspect_serial_active],1
 jne .done
 mov ax,[uart_rx_count]
.done: ret
_aspect_serial_read:
 push bx
 push si
 push di
 mov word [serial_unread_valid],0
 cmp word [_aspect_serial_active],1
 jne .empty
 cmp word [_aspect_serial_status],0
 jne .empty
 pushf
 cli
 mov bx,[uart_rx_read]
 mov [serial_unread_slot],bx
 call uart_receive_byte
 cmp ax,0xffff
 je .read_done
 mov word [serial_unread_valid],1
.read_done:
 popf
 pop di
 pop si
 pop bx
 ret
.empty:
 mov ax,0xffff
 pop di
 pop si
 pop bx
 ret
; Bounded one-shot rollback of the last successful API dequeue. Unlike native
; ABDE, never enables IF unconditionally and never increments a full ring.
; Ring cells retain raw bytes even when the API read applied its7-bit mask.
_aspect_serial_unread:
 push bx
 pushf
 cli
 mov ax,4
 cmp word [serial_unread_valid],1
 mov word [serial_unread_valid],0
 jne .done
 cmp word [_aspect_serial_active],1
 jne .done
 cmp word [_aspect_serial_status],0
 jne .done
 cmp word [uart_rx_dropped],0
 jne .overflow
 cmp word [uart_rx_count],4096
 jae .overflow
 mov bx,[serial_unread_slot]
 cmp bx,uart_rx_buffer
 jb .done
 cmp bx,uart_rx_buffer+4095
 ja .done
 mov ax,bx
 inc ax
 cmp bx,uart_rx_buffer+4095
 jne .expected
 mov ax,uart_rx_buffer
.expected:
 cmp ax,[uart_rx_read]
 mov ax,4
 jne .done
 mov [uart_rx_read],bx
 inc word [uart_rx_count]
 xor ax,ax
 jmp .done
.overflow:
 mov word [_aspect_serial_status],5
 mov ax,5
.done:
 popf
 pop bx
 ret
_aspect_serial_try_write:
 push bp
 mov bp,sp
 cmp word [_aspect_serial_active],1
 jne .bad
 cmp word [_aspect_serial_status],0
 jne .bad
 cmp byte [uart_flow_pending],0
 jne .waiting
 mov ax,[bp+4]
 call uart_try_write
 mov ax,0
 jnc .done
 inc ax
 jmp .done
.waiting: mov ax,1
 jmp .done
.bad: mov ax,2
.done: pop bp
 ret
global _aspect_serial_tx_empty
_aspect_serial_tx_empty:
 mov dx,[uart_port_lsr]
 in al,dx
 and ax,0x40
 ret
_aspect_serial_poll:
 cmp word [_aspect_serial_active],1
 jne .status
 cmp word [uart_rx_dropped],0
 je .flow
 mov word [_aspect_serial_status],5
.flow:
 call uart_poll_flow
.status:
 mov ax,[_aspect_serial_status]
 ret
global _aspect_serial_psp
_aspect_serial_psp:
 push bx
 mov ah,0x62
 int 0x21
 mov ax,bx
 pop bx
 ret
_aspect_serial_ticks:
 push es
 mov ax,0x40
 mov es,ax
 pushf
 cli
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 ret
_aspect_serial_backend_close:
 push bx
 push si
 push di
 push es
 mov word [serial_unread_valid],0
 cmp word [_aspect_serial_active],1
 jne .done
 ; Never spin or consume RX to hide a lifecycle failure. Parent handback is a
 ; separate contract; a caller closing with unread input receives explicit6.
 cmp word [_aspect_serial_status],0
 jne .quiet
 cmp word [_aspect_serial_handoff_enabled],1
 je .pending
 cmp word [uart_rx_count],0
 je .pending
 mov word [_aspect_serial_status],6
.pending:
 mov dx,[uart_port_lsr]
 in al,dx
 test al,0x40
 jnz .quiet
 .notempty:
 cmp word [_aspect_serial_status],0
 jne .quiet
 mov word [_aspect_serial_status],7
.quiet:
 mov dx,[uart_port_mcr]
 in al,dx
 and al,0xfd
 out dx,al
 call uart_mask_irq
 mov dx,[uart_port_lcr]
 in al,dx
 and al,0x7f
 out dx,al
 mov dx,[uart_port_ier]
 xor al,al
 out dx,al
 push word [serial_vector]
 call uart_restore_interrupt
 add sp,2
 call uart_restore_hardware_state
 mov word [_aspect_serial_active],0
.done:
 mov ax,[_aspect_serial_status]
 pop es
 pop di
 pop si
 pop bx
 ret
; Unreachable legacy blocking UART services are explicit fail-stop boundaries.
; Only the bounded entrypoints above are part of this backend's API.
global pcplus_seconds,pcplus_flow_bell,pcplus_flow_message,pcplus_escape_pressed
 global pcplus_screen_restore,pcplus_screen_save
pcplus_seconds:
pcplus_flow_bell:
pcplus_flow_message:
pcplus_escape_pressed:
pcplus_screen_restore:
pcplus_screen_save:
 mov ax,0x4c7f
 int 0x21
SEGMENT _DATA public class=DATA use16
%macro w 2
 global %1
 %1: dw %2
%endmacro
%macro b 2
 global %1
 %1: db %2
%endmacro
w _aspect_serial_active,0
w _aspect_serial_status,0
w _aspect_serial_handoff_enabled,0
w serial_unread_valid,0
w serial_unread_slot,0
w serial_vector,12
serial_bases: dw 0x3f8,0x2f8,0x3e8,0x2e8
serial_vectors: dw 12,11,12,11
w uart_port_index,0
w uart_software_flow,0
w uart_hardware_flow,0
w uart_tx_paused,0
b uart_flow_pending,0
b uart_xoff_sent,0
b uart_rts_lowered,0
w uart_rx_read,uart_rx_buffer
w uart_rx_write,uart_rx_buffer
w uart_rx_last,uart_rx_buffer+4095
w uart_rx_dropped,0
global _aspect_serial_rx_count,aspect_serial_rx_count
aspect_serial_rx_count:
_aspect_serial_rx_count:
w uart_rx_count,0
w uart_rx_mask,255
w uart_port_lcr,0x3fb
w uart_port_mcr,0x3fc
w uart_port_msr,0x3fe
w uart_port_lsr,0x3fd
w uart_port_thr,0x3f8
w uart_port_ier,0x3f9
w uart_port_rbr,0x3f8
b uart_saved_pic,0
b uart_saved_lcr,0
b uart_saved_mcr,0
b uart_saved_ier,0
b uart_saved_dll,0
b uart_saved_dlm,0
w uart_irq_indices,4
 dw 3,4,3
w uart_irq_enable_masks,255
 dw 255,255,0xf7,0xef
w uart_irq_disable_masks,0
 dw 0,0,8,16
global uart_flow_message,uart_flow_screen_save
uart_flow_message: db 0
uart_flow_screen_save: db 0
SEGMENT _BSS public class=BSS use16
global uart_rx_buffer
uart_rx_buffer: resb 4096

; C ABI aliases to the same recovered driver state (no duplicate storage).
global _uart_rx_buffer,_uart_rx_read,_uart_rx_write,_uart_rx_count,_uart_software_flow,_uart_flow_pending,_uart_rx_mask
_uart_rx_buffer equ uart_rx_buffer
_uart_rx_read equ uart_rx_read
_uart_rx_write equ uart_rx_write
_uart_rx_count equ uart_rx_count
_uart_software_flow equ uart_software_flow
_uart_flow_pending equ uart_flow_pending
_uart_rx_mask equ uart_rx_mask
SEGMENT STACK stack class=STACK use16
GROUP DGROUP _DATA _BSS STACK

; Shared maintained pure accounting patch, applied only to the child's private
; directory snapshot before UART admission. No filesystem or automatic TX.
%include "../directory_accounting/patch.asm"
