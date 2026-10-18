; Maintained PROGRAM scheduling, DOS child handoff and fixed80x25 restoration.
; Native433d/896a remain separately recovered; this is the small-model host policy.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_break_hold
extern process_psp,process_keep_paragraphs,process_minimum_paragraphs
extern terminal_stack_top,terminal_far_storage_end,_program_execute
extern terminal_snapshot_image_end,browser_screen_end,ed_screen_end
extern terminal_clock_ticks,terminal_macro_tx_epoch,terminal_tx_count
extern terminal_quit,terminal_exit_code,connection_state
extern uart_port_lsr,uart_port_thr,uart_port_lcr,uart_port_ier,uart_port_mcr
extern uart_port_index,uart_irq_indices,uart_irq_enable_masks
extern uart_software_flow,uart_hardware_flow,uart_flow_pending,uart_xoff_sent
extern uart_rts_lowered,uart_rx_count,uart_rx_dropped
extern uart_mask_irq,uart_restore_interrupt,uart_install_interrupt
extern uart_set_baud_divisor,uart_set_line_control
extern terminal_irq_vector,terminal_baud_low,terminal_baud_high
extern terminal_parity,terminal_data_bits,terminal_stop_bits
extern terminal_connection_notice,terminal_connection_notice_restore
extern terminal_capture_before_program
extern terminal_monitor_active
extern terminal_controller_active
extern _process_run,terminal_setup_tail
extern terminal_setup_prepare,terminal_setup_complete,terminal_setup_return_prompt
extern terminal_setup_key_consumed,terminal_setup_link_status
extern terminal_setup_profile_finish
global terminal_program_initialize,terminal_program_start,terminal_program_poll
global terminal_program_cancel
global terminal_program_prepare_link

; AX startup PSP. Retain every static segment, including far metadata/history.
; Preserve all registers, including AX needed by command-tail parsing next.
terminal_program_initialize:
 push ax
 push bx
 push cx
 push dx
 mov [process_psp],ax
 mov dx,ds
 mov bx,terminal_stack_top
 call .paragraphs
 add dx,bx
 %macro keep_static_end 1
 mov ax,seg %1
 mov bx,%1
 call .paragraphs
 add ax,bx
 cmp ax,dx
 jbe %%done
 mov dx,ax
%%done:
 %endmacro
 keep_static_end terminal_far_storage_end
 keep_static_end terminal_snapshot_image_end
 keep_static_end browser_screen_end
 keep_static_end ed_screen_end
 keep_static_end program_screen_end
 mov ax,dx
 sub ax,[process_psp]
 mov [process_keep_paragraphs],ax
 mov [process_minimum_paragraphs],ax
 pop dx
 pop cx
 pop bx
 pop ax
 ret
.paragraphs:
 ; Round OFFSET upward without overflowing a near16-bit addition.
 mov cx,bx
 shr bx,1
 shr bx,1
 shr bx,1
 shr bx,1
 and cx,15
 jz .rounded
 inc bx
.rounded:
 ret

; AX near stored command1..51.0 queued,1 invalid,2 busy,3 modem owns RX.
terminal_program_start:
 push bp
 push si
 push di
 push es
 cmp word [uart_break_hold],0
 jne .busy
 cmp word [terminal_controller_active],0
 jne .busy
 cmp word [terminal_monitor_active],0
 jne .busy
 cmp word [terminal_program_pending],0
 jne .busy
 cmp word [terminal_program_active],0
 jne .busy
 cmp word [connection_state],0
 je .validate
 cmp word [connection_state],6
 jne .connection
.validate:
 mov si,ax
 or si,si
 jz .invalid
 xor cx,cx
.scan:
 cmp byte [si],0
 je .validated
 cmp byte [si],13
 je .invalid
 cmp byte [si],10
 je .invalid
 cmp cx,51
 jae .invalid
 inc si
 jz .invalid
 inc cx
 jmp .scan
.validated:
 or cx,cx
 jz .invalid
 mov si,ax
 push ds
 pop es
 mov di,terminal_program_command
 inc cx
 cld
 rep movsb
 mov word [terminal_program_pending],1
 mov word [terminal_program_kind],0
 mov word [terminal_program_status],1
 mov byte [program_pause_sent],0
 mov ax,[terminal_macro_tx_epoch]
 mov [program_tx_epoch],ax
 call program_now
 call program_progress
 xor ax,ax
 jmp .done
.invalid:
 mov ax,1
 jmp .done
.busy:
 mov ax,2
 jmp .done
.connection:
 mov ax,3
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Called only by main, never from parser callbacks or a DOS/BIOS interrupt.
; Drain existing replies and the physical shift register before pausing RX.
terminal_program_poll:
 push bp
 push si
 push di
 push es
 cmp word [terminal_program_pending],0
 je .done
 cmp word [terminal_quit],0
 jne .cancel
 cmp word [connection_state],0
 je .clock
 cmp word [connection_state],6
 jne .cancel
.clock:
 cmp word [uart_rx_dropped],0
 jne .overflow
 call program_now
 mov ax,[terminal_macro_tx_epoch]
 cmp ax,[program_tx_epoch]
 je .deadline
 mov [program_tx_epoch],ax
 call program_progress
.deadline:
 mov ax,[program_now_tick]
 mov dx,[program_now_tick+2]
 sub ax,[program_progress_tick]
 sbb dx,[program_progress_tick+2]
 jnc .elapsed
 add ax,0x00b0
 adc dx,0x0018
.elapsed:
 or dx,dx
 jnz .timeout
 cmp ax,36
 jae .timeout
 cmp word [terminal_tx_count],0
 jne .done
 cmp byte [uart_flow_pending],0
 jne .done
 mov dx,[uart_port_lsr]
 in al,dx
 and al,0x60
 cmp al,0x60
 jne .done
 cmp word [uart_software_flow],0
 je .launch
 cmp byte [uart_xoff_sent],0
 jne .launch
 ; THRE/TEMT are ready. Control flow bypasses peer CTS/XOFF restrictions.
 mov dx,[uart_port_thr]
 mov al,0x13
 out dx,al
 mov byte [uart_xoff_sent],1
 mov byte [program_pause_sent],1
 call program_progress
 jmp .done ; Wait for this XOFF's physical shift-register completion too.
.launch:
 call terminal_capture_before_program
 cmp ax,2
 je .printer_wait
 or ax,ax
 jnz .cancel
 call terminal_connection_notice_restore
 ; The current live renderer is fixed80x25 mode3/page0. Reject other BIOS views.
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .view
 cmp ah,80
 jne .view
 or bh,bh
 jnz .view
 mov ah,3
 xor bh,bh
 int 0x10
 mov [program_cursor],dx
 mov [program_shape],cx
 push ds
 push es
 mov ax,[program_screen_segment]
 mov es,ax
 mov di,program_screen
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov cx,2000
 cld
 rep movsw
 pop es
 pop ds
 mov word [terminal_program_pending],0
 mov word [terminal_program_active],1
 mov word [terminal_program_status],2
 ; Preserve DTR, lower RTS, mask the UART and release its vector for the child.
 ; No parent ISR points into parent memory during DOS EXEC or its pause prompt.
 mov dx,[uart_port_mcr]
 in al,dx
 mov [program_mcr],al
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
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
 mov ax,terminal_program_result
 push ax
 cmp word [terminal_program_kind],1
 je .setup_child
 mov ax,terminal_program_command
 push ax
 call _program_execute
 add sp,4
 jmp .child_status
.setup_child:
 call terminal_setup_prepare
 or ax,ax
 jnz .setup_denied
 mov ax,terminal_setup_tail
 push ax
 mov ax,program_setup_executable
 push ax
 call _process_run
 add sp,6
 jmp .child_status
.setup_denied:
 add sp,2 ;Release only the already-pushed result pointer; no EXEC happened.
.child_status:
 or ax,ax
 jnz .record_status
 cmp word [terminal_program_kind],1
 jne .record_status
 cmp word [terminal_program_result+4],0
 je .record_status
 mov ax,1
.record_status:
 or ax,ax
 mov word [terminal_program_status],4
 jz .child_finished
 mov word [terminal_program_status],5
.child_finished:
 ; A child may leave its UART ISR/interrupt-enable state behind. Quiet that
 ; port and restore its baseline vector before drawing or waiting for a key.
 call program_quiet_uart
 cmp word [terminal_program_kind],1
 jne .return_prompt
 call terminal_setup_complete
.return_prompt:
 ; Original PROGRAM asks for a local key after the command. BIOS output avoids
 ; introducing DOS text-output/CTRL-C checks while the port is handed off.
 mov si,program_return_prompt
 cmp word [terminal_program_kind],1
 jne .check_error
 call terminal_setup_return_prompt
.check_error:
 cmp word [terminal_program_status],5
 jne .prompt
 mov si,program_error_prompt
.prompt:
 lodsb
 or al,al
 jz .key
 mov ah,0x0e
 xor bh,bh
 mov bl,7
 int 0x10
 jmp .prompt
.key:
 cmp word [terminal_program_kind],1
 jne .read_return_key
 cmp word [terminal_setup_key_consumed],1
 je .restore_screen
.read_return_key:
 xor ax,ax
 int 0x16
.restore_screen:
 ; Recreate the supported video mode even if a child left graphics or new fonts.
 mov ax,3
 int 0x10
 mov ax,0xb800
 mov es,ax
 push ds
 mov ax,[program_screen_segment]
 mov ds,ax
 mov si,program_screen
 xor di,di
 mov cx,2000
 cld
 rep movsw
 pop ds
 mov cx,[program_shape]
 mov ah,1
 int 0x10
 mov dx,[program_cursor]
 xor bh,bh
 mov ah,2
 int 0x10
 cmp word [terminal_program_kind],1
 jne .restore_port
 call terminal_setup_profile_finish
.restore_port:
 call program_restore_uart
 mov word [terminal_program_active],0
 call program_resume_flow
 jmp .done
.printer_wait:
 ; Printer has its own bounded progress timer; keep the UART handoff deadline
 ; fresh while the foreground main loop drains it before DOS EXEC.
 call program_progress
 jmp .done
.cancel:
 call terminal_program_cancel
 jmp .done
.overflow:
 call terminal_program_cancel
 mov word [terminal_exit_code],6
 mov word [terminal_quit],1
 jmp .done
.timeout:
 call terminal_program_cancel
 mov word [terminal_program_status],8
 mov si,program_busy_notice
 call terminal_connection_notice
 jmp .done
.view:
 call terminal_program_cancel
 mov word [terminal_program_status],9
 mov si,program_view_notice
 call terminal_connection_notice
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

program_quiet_uart:
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
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
 ret

program_restore_uart:
 ; A child may change this port/vector. Keep it masked until our vector and
 ; configured format are restored. Never overwrite the saved startup baseline.
 call uart_mask_irq
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jz .no_overrun
 cmp word [uart_rx_dropped],0xffff
 je .no_overrun
 inc word [uart_rx_dropped]
.no_overrun:
 mov dx,[uart_port_lcr]
 in al,dx
 and al,0x7f
 out dx,al
 mov dx,[uart_port_ier]
 xor al,al
 out dx,al
 push word [terminal_irq_vector]
 call uart_restore_interrupt
 add sp,2
 push word [terminal_baud_high]
 push word [terminal_baud_low]
 call uart_set_baud_divisor
 add sp,4
 push word [terminal_stop_bits]
 push word [terminal_data_bits]
 push word [terminal_parity]
 call uart_set_line_control
 add sp,6
 push word [terminal_irq_vector]
 call uart_install_interrupt
 add sp,2
 ; Do not call uart_enable here: it reads/discards RBR. Preserve pending input.
 mov al,[program_mcr]
 cmp word [terminal_program_kind],1
 jne .old_rts
 cmp word [terminal_setup_link_status],1
 jne .old_rts
 or al,2 ;An accepted flow change must release the old port's lowered RTS.
.old_rts:
 cmp word [uart_hardware_flow],0
 je .mcr
 cmp byte [uart_rts_lowered],0
 je .mcr
 and al,0xfd
.mcr:
 mov dx,[uart_port_mcr]
 out dx,al
 mov dx,[uart_port_ier]
 mov al,1
 out dx,al
 in al,0x21
 mov bx,[uart_port_index]
 shl bx,1
 mov bx,[uart_irq_indices+bx]
 shl bx,1
 and ax,[uart_irq_enable_masks+bx]
 out 0x21,al
 ret

; UART remains IRQ-masked, IER0 and RTS-low. Restore the old effective framing
; after a child, wait for TEMT, and release a software pause at that OLD format
; before the caller changes baud/line/flow globals. AX0 ready,1 deadline/overrun.
; No startup snapshot is overwritten and no RBR byte is read.
terminal_program_prepare_link:
 push bp
 push si
 push di
 push es
 push word [terminal_baud_high]
 push word [terminal_baud_low]
 call uart_set_baud_divisor
 add sp,4
 push word [terminal_stop_bits]
 push word [terminal_data_bits]
 push word [terminal_parity]
 call uart_set_line_control
 add sp,6
 call program_now
 call program_progress
 xor di,di ;0 before XON,1 waiting for its physical completion.
.wait:
 mov dx,[uart_port_lsr]
 in al,dx
 test al,2
 jnz .overrun
 and al,0x60
 cmp al,0x60
 jne .deadline
 or di,di
 jnz .ready
 cmp word [uart_software_flow],0
 je .ready
 cmp byte [uart_xoff_sent],0
 jne .xon
 cmp byte [uart_flow_pending],0x11
 jne .ready
.xon:
 mov dx,[uart_port_thr]
 mov al,0x11
 out dx,al
 mov byte [uart_flow_pending],0
 mov byte [uart_xoff_sent],0
 mov byte [program_pause_sent],0
 inc di
 jmp .wait
.deadline:
 call program_now
 mov ax,[program_now_tick]
 mov dx,[program_now_tick+2]
 sub ax,[program_progress_tick]
 sbb dx,[program_progress_tick+2]
 jnc .elapsed
 add ax,0x00b0
 adc dx,0x0018
.elapsed:
 or dx,dx
 jnz .failed
 cmp ax,36
 jb .wait
 jmp .failed
.overrun:
 cmp word [uart_rx_dropped],0xffff
 je .failed
 inc word [uart_rx_dropped]
.failed:
 mov ax,1
 jmp .done
.ready:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Release only this launch's added XOFF. Existing ring watermarks remain owned
; by the recovered driver; buffered input above128 bytes keeps its normal pause.
program_resume_flow:
 cmp byte [program_pause_sent],0
 je .done
 mov byte [program_pause_sent],0
 cmp word [uart_rx_count],128
 ja .done
 mov byte [uart_xoff_sent],0
 mov byte [uart_flow_pending],0x11
.done:
 ret

terminal_program_cancel:
 push ax
 push cx
 push di
 push es
 cmp word [terminal_program_pending],0
 je .clear
 mov word [terminal_program_status],3
.clear:
 mov word [terminal_program_pending],0
 mov word [terminal_program_kind],0
 call program_resume_flow
 push ds
 pop es
 mov di,terminal_program_command
 xor ax,ax
 mov cx,26
 cld
 rep stosw
 pop es
 pop di
 pop cx
 pop ax
 ret

program_now:
 call terminal_clock_ticks
 mov [program_now_tick],ax
 mov [program_now_tick+2],dx
 ret
program_progress:
 mov ax,[program_now_tick]
 mov [program_progress_tick],ax
 mov ax,[program_now_tick+2]
 mov [program_progress_tick+2],ax
 ret

SEGMENT _DATA public align=16 class=DATA use16
global terminal_program_pending,terminal_program_active,terminal_program_status
global terminal_program_command,terminal_program_result
global terminal_program_kind
terminal_program_kind: dw 0 ;0 PROGRAM/COMSPEC,1 direct maintained settings editor.
terminal_program_pending: dw 0
terminal_program_active: dw 0
terminal_program_status: dw 0
terminal_program_result: times 4 dw 0
terminal_program_command: times 52 db 0
program_now_tick: dd 0
program_progress_tick: dd 0
program_tx_epoch: dw 0
program_pause_sent: db 0
program_mcr: db 0
program_cursor: dw 0
program_shape: dw 0
global program_screen_segment
program_screen_segment: dw seg program_screen
program_return_prompt: db 13,10,'Press a key to return to the terminal.',0
program_error_prompt: db 13,10,'Program could not run. Press a key to return.',0
program_setup_executable: db 'PRMEDIT.EXE',0
program_busy_notice: db 'Program busy',0
program_view_notice: db 'Program view',0

SEGMENT UI_STORAGE public align=16 class=FAR_DATA use16
GROUP UI_GROUP UI_STORAGE
global program_screen,program_screen_end
program_screen: resb 4000
program_screen_end:
