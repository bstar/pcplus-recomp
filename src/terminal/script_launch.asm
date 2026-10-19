; Maintained Script menu -> existing drained PROGRAM owner -> direct ASPECT.
; The child owns an explicit raw UART lease; terminal rendering resumes later.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_kind,process_psp
extern terminal_translation_edit_executable,terminal_translation_edit_tail
extern _command_menu_script,_terminal_script_prepare
extern terminal_program_command,terminal_program_status
extern uart_rx_count,uart_rx_dropped,uart_rx_buffer,uart_rx_read,uart_rx_write
extern uart_port_lcr,uart_port_thr,uart_software_flow,uart_hardware_flow
extern terminal_port_number,terminal_irq_vector
extern uart_rts_lowered,terminal_parser_active,terminal_ansi_wait_active
extern terminal_translation_enabled,terminal_translation_mode,terminal_translation_table,uart_rx_mask
script_translation_policy:
 mov ax,[terminal_translation_mode]
 cmp ax,2
 ja .bad
 mov dx,255
 xor cx,cx
 cmp ax,1
 jne .mask
 inc cx
.mask:
 cmp ax,2
 jne .check
 mov dx,127
.check:
 cmp [terminal_translation_enabled],cx
 jne .bad
 cmp [uart_rx_mask],dx
 jne .bad
 ret
.bad:
 mov ax,0xffff
 ret

extern uart_poll_flow,keyboard_poll,terminal_read_key,terminal_defer_key
extern terminal_quit,terminal_exit_code,uart_port_lsr
global terminal_script_start,terminal_script_prepare,terminal_script_complete
 global terminal_script_return_key
terminal_script_start:
 push si
 push di
 push es
 call script_admit
 or ax,ax
 jnz .done
 push ds
 pop es
 cld
 ; PROGRAM validates/copies this stored marker; never invokes it via COMSPEC
 ; because kind4 is installed before the foreground safe point can run.
 mov ax,script_marker
 call terminal_program_start
 or ax,ax
 jnz .done
 mov si,_command_menu_script
 mov di,terminal_translation_edit_tail
 mov al,' '
 stosb
 mov cx,64
.copy:
 lodsb
 stosb
 or al,al
 jz .queued
 loop .copy
 ; Menu guarantees a terminator; defense against an external synthetic action.
 mov byte [terminal_translation_edit_tail+64],0
.queued:
 mov word [terminal_program_kind],4
.done:
 pop es
 pop di
 pop si
 ret
; Final guard after parent IRQ quiet: no parser or parent ring state can be
; stranded in another segment. Hardware RBR is left for the child ISR.
script_admit:
 mov ax,1
 cmp word [uart_rx_count],0
 jne .done
 cmp word [uart_rx_dropped],0
 jne .done
 cmp word [terminal_parser_active],0
 jne .done
 cmp word [terminal_ansi_wait_active],0
 jne .done
 xor ax,ax
.done: ret
terminal_script_prepare:
 mov word [script_handoff+22],0 ;No stale prior publication on failed admission.
 call script_admit
 or ax,ax
 jnz .done
 call script_translation_policy
 cmp ax,2
 ja .bad_policy
 mov [script_handoff+26],ax
 xor bx,bx
 cmp ax,1
 jne .policy_staged
 mov bx,terminal_translation_table
.policy_staged:
 mov [script_handoff+24],bx
 ; Save and restore LCR around divisor latch reads, never read/discard RBR.
 mov dx,[uart_port_lcr]
 in al,dx
 and ax,0x7f
 mov [script_lcr],ax
 ; script_lcr is the actual validated non-DLAB LCR.
 mov al,[script_lcr]
 or al,0x80
 out dx,al
 mov dx,[uart_port_thr]
 in al,dx
 mov bl,al
 inc dx
 in al,dx
 mov bh,al
 mov [script_divisor],bx
 mov dx,[uart_port_lcr]
 mov al,[script_lcr]
 out dx,al
 ; The terminal installs its selected UART in native slot0. That slot is not
 ; the BIOS COM number. The child uses the actual one-based session selection.
 mov ax,[terminal_port_number]
 dec ax
 cmp ax,3
 ja .bad_policy
 mov bx,ax
 shl bx,1
 mov dx,[cs:script_bases+bx]
 cmp dx,[uart_port_thr]
 jne .bad_policy
 mov dx,[cs:script_vectors+bx]
 cmp dx,[terminal_irq_vector]
 jne .bad_policy ;The current child ABI supports standard IRQs only.
 mov [_script_port_index],ax
 mov ax,[uart_software_flow]
 mov [_script_soft_flow],ax
 mov ax,[uart_hardware_flow]
 mov [_script_hard_flow],ax
 mov ax,terminal_translation_edit_tail
 push ax
 mov ax,terminal_translation_edit_executable
 push ax
 push word [process_psp]
 call _terminal_script_prepare
 add sp,6
.done: ret
.bad_policy:
 mov ax,1
 ret
script_bases: dw 0x3f8,0x2f8,0x3e8,0x2e8
script_vectors: dw 12,11,12,11

; Serviced return-key wait. Parent IRQ buffers incoming bytes; only bounded
; foreground flow control runs here. Never parse/render onto the child console.
terminal_script_return_key:
.loop:
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jz .counter
 cmp word [uart_rx_dropped],0xffff
 je .counter
 inc word [uart_rx_dropped]
.counter:
 cmp word [uart_rx_dropped],0
 jne .overflow
 call uart_poll_flow
 cmp word [terminal_quit],0
 jne .done
 call keyboard_poll
 or ax,ax
 jz .idle
 call terminal_read_key
 cmp ax,0x2d00
 jne .hangup
 mov word [terminal_quit],1
 jmp .done
.hangup:
 cmp ax,0x2300
 jne .done
 call terminal_defer_key ;Run normal hangup only after restoring live screen.
.done: ret
.idle:
 sti
 hlt
 jmp .loop
.overflow:
 mov word [terminal_exit_code],6
 mov word [terminal_quit],1
 ret
SEGMENT _DATA public class=DATA use16
script_marker: db 'ASPECT',0

; Parent-only validated ASIO publication. Runs with child IRQ quiet and before
; return prompt/parent ISR restoration. It never accepts pointers from child.
SEGMENT _TEXT
terminal_script_complete:
 cmp word [script_handoff+22],1
 jne .missing
 cmp word [script_handoff],0x5341
 jne .bad
 cmp word [script_handoff+2],0x4f49
 jne .bad
 cmp word [script_handoff+4],2
 jne .bad
 cmp word [script_handoff+6],28
 jne .bad
 mov ax,[process_psp]
 cmp [script_handoff+8],ax
 jne .bad
 mov dx,ds
 cmp [script_handoff+10],dx
 jne .bad
 cmp word [script_handoff+12],uart_rx_buffer
 jne .bad
 cmp word [script_handoff+14],4096
 jne .bad
 xor ax,dx
 xor ax,uart_rx_buffer
 xor ax,0xa510
 xor ax,[script_handoff+24]
 xor ax,[script_handoff+26]
 cmp [script_handoff+20],ax
 jne .bad
 mov ax,[terminal_translation_mode]
 cmp [script_handoff+26],ax
 jne .bad
 xor bx,bx
 cmp ax,1
 jne .check_table
 mov bx,terminal_translation_table
.check_table:
 cmp [script_handoff+24],bx
 jne .bad
 mov ax,[script_handoff+16]
 cmp ax,4096
 ja .bad
 mov [uart_rx_count],ax
 mov word [uart_rx_read],uart_rx_buffer
 mov bx,uart_rx_buffer
 cmp ax,4096
 je .wrapped
 add bx,ax
.wrapped:
 mov [uart_rx_write],bx
 cmp word [uart_hardware_flow],0
 je .status
 cmp ax,3072
 jb .status
 mov byte [uart_rts_lowered],1
.status:
 cmp word [script_handoff+18],0
 je .done
.bad:
 mov word [terminal_program_status],5
 ret
.missing:
 ; Failed EXEC has no child publication; preserve its existing failure.
 cmp word [terminal_program_status],4
 je .bad
.done: ret
SEGMENT _DATA
global _script_handoff,_script_divisor,_script_lcr
_script_handoff:
script_handoff: times 14 dw 0
_script_divisor:
script_divisor: dw 0
_script_lcr:
script_lcr: dw 0
global _script_parent_ring,_script_port_index,_script_soft_flow,_script_hard_flow
_script_parent_ring: dw uart_rx_buffer
_script_port_index: dw 0
_script_soft_flow: dw 0
_script_hard_flow: dw 0
