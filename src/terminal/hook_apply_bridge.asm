BITS 16
CPU 8086
%ifdef TERMINAL_HOOK_APPLY
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
NEAR_NAMED_SERVICE hook_apply_display,terminal_apply_live_configuration
NEAR_NAMED_SERVICE hook_prepare_link,terminal_program_prepare_link
NEAR_NAMED_SERVICE hook_port_move,terminal_port_handoff
NEAR_NAMED_SERVICE hook_port_check,terminal_port_check
NEAR_NAMED_SERVICE hook_apply_notice,terminal_connection_notice
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
%macro argument 1
 global _%1
 extern %1 %+ _resident
 _%1:
 push bp
 mov bp,sp
 mov ax,[bp+6]
 call far %1 %+ _resident
 pop bp
 retf
%endmacro
argument hook_apply_display
argument hook_port_move
argument hook_port_check
global _hook_prepare_link
_hook_prepare_link:
 call far hook_prepare_link_resident
 retf
global _terminal_hook_apply_epoch,_terminal_hook_apply_seal
_terminal_hook_apply_epoch: dw 0
_terminal_hook_apply_seal: dw 0
global _terminal_hook_last_status
_terminal_hook_last_status: dw 0
global _terminal_hook_completed_status
_terminal_hook_completed_status: dw 0
global terminal_hook_apply_notice
terminal_hook_apply_notice:
 push bp
 mov bp,sp
 sub sp,16
 push si
 push di
 push cx
 push es
 push ds
 pop es
 mov si,.text
 lea di,[bp-16]
 mov cx,14
.copy:
 mov al,[cs:si]
 inc si
 stosb
 loop .copy
 lea si,[bp-16]
 call far hook_apply_notice_resident
 pop es
 pop cx
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
.text: db 'Helper failed',0
extern terminal_program_active,terminal_program_kind,terminal_program_status
extern hardware_active,vector_active,uart_port_rbr,uart_port_thr,uart_port_ier
extern uart_port_lcr,uart_port_mcr,uart_port_lsr,uart_port_msr
extern uart_irq_indices,uart_irq_disable_masks,terminal_irq_vector,terminal_port_number
extern uart_previous_irq_offset,uart_previous_irq_segment,uart_rx_dropped,uart_rx_count,terminal_tx_count
global _hook_apply_uart_check
_hook_apply_uart_check:
 push bp
 mov bp,sp
 push si
 push di
 push es
 cmp byte [hardware_active],1
 jne .bad
 cmp byte [vector_active],1
 jne .bad
 cmp word [terminal_program_active],1
 jne .bad
 cmp word [terminal_program_kind],5
 jne .bad
 cmp word [terminal_program_status],4
 jne .bad
 cmp word [uart_rx_dropped],0
 jne .bad
 mov bx,[terminal_port_number]
 dec bx
 cmp bx,3
 ja .bad
 shl bx,1
 mov ax,0x40
 mov es,ax
 mov dx,[es:bx]
 or dx,dx
 jz .bad
 cmp dx,0xfff8
 ja .bad
 cmp dx,[uart_port_rbr]
 jne .bad
 cmp dx,[uart_port_thr]
 jne .bad
 inc dx
 cmp dx,[uart_port_ier]
 jne .bad
 add dx,2
 cmp dx,[uart_port_lcr]
 jne .bad
 inc dx
 cmp dx,[uart_port_mcr]
 jne .bad
 inc dx
 cmp dx,[uart_port_lsr]
 jne .bad
 inc dx
 cmp dx,[uart_port_msr]
 jne .bad
 mov bx,[uart_irq_indices]
 cmp bx,3
 je .irq
 cmp bx,4
%ifdef TERMINAL_CUSTOM_IRQ
 je .irq
 cmp bx,5
 je .irq
 cmp bx,7
%endif
 jne .bad
.irq:
 mov ax,bx
 add ax,8
 cmp ax,[terminal_irq_vector]
 jne .bad
 shl bx,1
 in al,0x21
 test al,[uart_irq_disable_masks+bx]
 jz .bad
 mov ax,seg uart_previous_irq_offset
 mov es,ax
 mov si,[es:uart_previous_irq_offset]
 mov di,[es:uart_previous_irq_segment]
 mov ax,si
 or ax,di
 jz .bad
 xor ax,ax
 mov es,ax
 mov bx,[terminal_irq_vector]
 shl bx,1
 shl bx,1
 cmp si,[es:bx]
 jne .bad
 cmp di,[es:bx+2]
 jne .bad
 mov dx,[uart_port_lcr]
 in al,dx
 test al,0x80
 jnz .bad
 mov dx,[uart_port_ier]
 in al,dx
 or al,al
 jnz .bad
 mov dx,[uart_port_mcr]
 in al,dx
 test al,2
 jnz .bad
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jnz .overrun
 mov ah,al
 and al,0x60
 cmp al,0x60
 jne .bad
 test word [bp+6],15
 jz .ok
 test ah,1
 jnz .bad
 cmp word [uart_rx_count],0
 jne .bad
 cmp word [terminal_tx_count],0
 jne .bad
.ok:
 xor ax,ax
 jmp .done
.overrun:
 cmp word [uart_rx_dropped],65535
 je .bad
 inc word [uart_rx_dropped]
.bad:
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bp
 retf
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%macro entry 2
 global _%1
 extern _%2 %+ _impl
 _%1:
 push bp
 mov bp,sp
 push word [bp+8]
 push word [bp+6]
 call _%2 %+ _impl
 mov sp,bp
 pop bp
 retf
%endmacro
entry hook_xlt_check,xlt_live_commit_check
entry hook_xlt_publish,xlt_live_publish
%endif
