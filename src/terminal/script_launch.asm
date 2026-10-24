; Maintained Script menu -> existing drained PROGRAM owner -> direct ASPECT.
; The child owns an explicit raw UART lease; terminal rendering resumes later.
BITS 16
CPU 8086
%include "directory_live.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_kind,process_psp
extern terminal_translation_edit_executable,terminal_translation_edit_tail
extern _command_menu_script,_terminal_script_prepare
extern terminal_program_command,terminal_program_status
extern uart_rx_count,uart_rx_dropped,uart_rx_buffer,uart_rx_read,uart_rx_write
extern uart_port_lcr,uart_port_thr,uart_software_flow,uart_hardware_flow
extern uart_tx_paused
extern terminal_port_number,terminal_irq_vector
%ifdef TERMINAL_CUSTOM_IRQ
extern uart_irq_indices
%endif
extern uart_rts_lowered,terminal_parser_active,terminal_ansi_wait_active
extern terminal_translation_enabled,terminal_translation_mode,terminal_translation_table,uart_rx_mask
extern terminal_directory_context_valid,terminal_directory_context
extern terminal_program_active,terminal_program_pending,_command_menu_active,_redisplay_active
extern directory_pending,directory_pending_count,directory_pending_year,directory_pending_month,directory_pending_day
extern terminal_render_prepare,terminal_render_revoke,terminal_render_validate
global terminal_directory_script_connected
; One call per successful directory connection. Reuse the manual launch owner
; and filename storage; no separate armed flag or mutable directory bytes.
terminal_directory_script_connected:
 push bp
 push si
 push di
 push es
 cmp word [terminal_directory_context_valid],0
 je .done
 mov ax,[terminal_program_active]
 or ax,[terminal_program_pending]
 or ax,[_command_menu_active]
 or ax,[_redisplay_active]
 jnz .done
 mov si,terminal_directory_context+DLC_RECORD+0x34
 cmp byte [si],0
 je .done
 cmp byte [si],' '
 je .done
 push ds
 pop es
 mov di,_command_menu_script
 mov cx,9
 xor bx,bx
 cld
.copy:
 lodsb
 or al,al
 jz .suffix
 cmp al,'a'
 jb .upper
 cmp al,'z'
 ja .upper
 sub al,32
.upper:
 cmp al,0x5c
 jne .dot
 xor bx,bx
.dot:
 cmp al,'.'
 jne .store
 inc bx
.store:
 stosb
 loop .copy
 jmp .done ;Startup validated NUL within9; retain defense against mutation.
.suffix:
 or bx,bx
 jnz .terminate
 mov ax,0x412e ;.A
 stosw
 mov ax,0x5853 ;SX
 stosw
.terminate:
 xor al,al
 stosb
 call terminal_script_start
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; AX selected entry0/1..200, BX near raw114-byte record or0. No new DATA.
script_directory_policy:
 xor ax,ax
 xor bx,bx
 cmp word [terminal_directory_context_valid],0
 je .done
 mov ax,[terminal_directory_context+DLC_ENTRY]
 or ax,ax
 jz .bad
 cmp ax,200
 ja .bad
 mov bx,terminal_directory_context+DLC_RECORD
.done: ret
.bad:
 mov ax,0xffff
 ret
; Derive pending accounting without changing the retained record or save baseline.
; Presence is independent of delta: the connection counter may wrap to zero.
script_projection_policy:
 xor ax,ax
 xor bx,bx
 xor cx,cx
 xor dx,dx
 cmp word [terminal_directory_context_valid],0
 je .done
 cmp byte [directory_pending],0
 je .done
 mov ax,[directory_pending_year]
 mov bx,[directory_pending_month]
 mov cx,[directory_pending_day]
 mov dx,[directory_pending_count]
.done: ret
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
 cmp word [uart_rx_count],4096
 ja .done
 cmp word [uart_rx_read],uart_rx_buffer
 jb .done
 cmp word [uart_rx_read],uart_rx_buffer+4096
 jae .done
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
 mov ax,[uart_tx_paused]
 cmp ax,1
 ja .bad_policy
 mov [_script_flow_flags],ax
 mov ax,[uart_rx_count]
 mov [script_handoff+16],ax
 xor bx,bx
 or ax,ax
 jz .preload_staged
 mov bx,[uart_rx_read]
 sub bx,uart_rx_buffer
.preload_staged:
 mov [script_handoff+18],bx
 call script_directory_policy
 cmp ax,200
 ja .bad_policy
 mov [_script_directory_entry],ax
 mov [_script_directory_record],bx
 call script_projection_policy
 mov [_script_directory_year],ax
 mov [_script_directory_month],bx
 mov [_script_directory_day],cx
 mov [_script_directory_delta],dx
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
%ifdef TERMINAL_CUSTOM_IRQ
 mov dx,[uart_irq_indices]
 cmp dx,3
 je .irq_ok
 cmp dx,4
 je .irq_ok
 cmp dx,5
 je .irq_ok
 cmp dx,7
 jne .bad_policy
.irq_ok:
 mov [_script_irq_index],dx
 add dx,8
%else
 mov dx,[cs:script_vectors+bx]
%endif
 cmp dx,[terminal_irq_vector]
 jne .bad_policy ;The vector must match the selected child lease.
 mov [_script_port_index],ax
 mov ax,[uart_software_flow]
 mov [_script_soft_flow],ax
 mov ax,[uart_hardware_flow]
 mov [_script_hard_flow],ax
 call far terminal_render_prepare
 or ax,ax
 jnz .bad_policy
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
%ifdef TERMINAL_TRAPS
 extern terminal_trap_poll
 call far terminal_trap_poll
%endif
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
 call far terminal_render_revoke
%ifdef TERMINAL_REGISTER_HANDOFF
 extern _terminal_register_extract,_terminal_register_commit,_terminal_register_discard
 xor ax,ax
 cmp word [terminal_program_status],4
 jne .register_success
 inc ax
.register_success:
 push ax
 mov ax,script_handoff
 push ax
 call far _terminal_register_extract
 add sp,4
 or ax,ax
 jnz .bad
%endif
 cmp word [script_handoff+22],1
 jne .missing
 cmp word [script_handoff],0x5341
 jne .bad
 cmp word [script_handoff+2],0x4f49
 jne .bad
 cmp word [script_handoff+4],6
 jne .bad
 cmp word [script_handoff+6],50
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
 xor ax,[_script_directory_entry]
 xor ax,[_script_directory_record]
 xor ax,[_script_directory_year]
 xor ax,[_script_directory_month]
 xor ax,[_script_directory_day]
 xor ax,[_script_directory_delta]
 xor ax,[_script_render_offset]
 xor ax,[_script_render_segment]
 xor ax,[_script_render_token]
 xor ax,[_script_render_version]
 xor ax,[uart_tx_paused] ;Original quiet-parent input, not child's output.
 mov bx,[_script_flow_flags]
 and bx,2 ;MODEM policy is immutable; peer pause may change in the child.
 xor ax,bx
 xor ax,[uart_rx_count]
 cmp word [uart_rx_count],0
 je .check_guard
 mov bx,[uart_rx_read]
 sub bx,uart_rx_buffer
 xor ax,bx
.check_guard:
 cmp [script_handoff+20],ax
 jne .bad
 call far terminal_render_validate
 or ax,ax
 jnz .bad
 call script_directory_policy
 cmp ax,[_script_directory_entry]
 jne .bad
 cmp bx,[_script_directory_record]
 jne .bad
 call script_projection_policy
 cmp ax,[_script_directory_year]
 jne .bad
 cmp bx,[_script_directory_month]
 jne .bad
 cmp cx,[_script_directory_day]
 jne .bad
 cmp dx,[_script_directory_delta]
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
 mov bx,[_script_flow_flags]
 cmp bx,3
 ja .bad
 cmp word [uart_software_flow],0
 jne .flow_valid
 test bl,1
 jnz .bad
.flow_valid:
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
 mov ax,[_script_flow_flags]
 and ax,1
 mov [uart_tx_paused],ax
 cmp word [script_handoff+18],0
%ifdef TERMINAL_REGISTER_HANDOFF
 jne .bad
 call far _terminal_register_commit
 or ax,ax
 jz .done
%else
 je .done
%endif
.bad:
%ifdef TERMINAL_REGISTER_HANDOFF
 call far _terminal_register_discard
%endif
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
global _script_directory_entry,_script_directory_record
_script_directory_entry: dw 0
_script_directory_record: dw 0
global _script_directory_year,_script_directory_month,_script_directory_day,_script_directory_delta
_script_directory_year: dw 0
_script_directory_month: dw 0
_script_directory_day: dw 0
_script_directory_delta: dw 0
global _script_render_offset,_script_render_segment,_script_render_token,_script_render_version
_script_render_offset: dw 0
_script_render_segment: dw 0
_script_render_token: dw 0
_script_render_version: dw 0
global _script_flow_flags
_script_flow_flags: dw 0
_script_divisor:
script_divisor: dw 0
_script_lcr:
script_lcr: dw 0
global _script_parent_ring,_script_port_index,_script_soft_flow,_script_hard_flow
_script_parent_ring: dw uart_rx_buffer
_script_port_index: dw 0
%ifdef TERMINAL_CUSTOM_IRQ
global _script_irq_index
_script_irq_index: dw 0
%endif
_script_soft_flow: dw 0
_script_hard_flow: dw 0
