; Maintained exclusive live ordinary-XMODEM owner over recovered native engine.
; No fixture callbacks. DS=SS, foreground only; ISR remains recovered UART code.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_break_hold
extern terminal_clock_ticks,terminal_quit,terminal_exit_code,connection_state
extern terminal_tx_count,terminal_tx_head,terminal_tx_buffer,terminal_macro_tx_epoch
extern terminal_macro_cancel,terminal_program_cancel,terminal_program_pending
extern uart_software_flow,uart_rx_count,uart_rx_dropped,uart_port_lsr,uart_port_msr
extern uart_receive_byte,uart_unreceive_byte,uart_try_write,uart_poll_flow
extern uart_rx_mask
extern keyboard_poll,terminal_read_key,terminal_baud_low,terminal_baud_high
extern terminal_transfer_ui_open,terminal_transfer_ui_restore,terminal_transfer_ui_receiving
extern terminal_transfer_ui_progress,terminal_connection_notice,terminal_connection_notice_restore
extern _terminal_transfer_store,_terminal_transfer_receive,_terminal_transfer_cleanup
extern _terminal_upload_store,_terminal_transfer_send,_terminal_upload_cleanup
extern _terminal_batch_store
extern _terminal_zmodem_store,_terminal_zmodem_files
extern _ymodem_current
extern terminal_upload_blocks_accepted
extern terminal_upload_accepted_bytes
extern terminal_upload_frame_active,terminal_upload_cancel_pending
extern terminal_upload_startup_ansi
extern _transfer_native_open,_transfer_native_write,_transfer_native_close,_transfer_download_result
extern session_setjmp,session_longjmp,session_blocks_accepted
extern terminal_monitor_active
extern terminal_controller_active
extern terminal_directory_mode
extern terminal_printer_barrier
GLOBAL terminal_transfer_start,terminal_transfer_poll,terminal_transfer_service
GLOBAL terminal_upload_start,terminal_transfer_direction
GLOBAL terminal_transfer_filter,terminal_transfer_shutdown
GLOBAL transfer_emit,transfer_maybe_unwind,transfer_protocol_started
GLOBAL terminal_transfer_accepted_progress

terminal_transfer_start:
 xor ax,ax
 jmp transfer_start_direction
terminal_upload_start:
 mov ax,1
transfer_start_direction:
 extern terminal_recording_owned_far
 push bp
 push si
 push di
 push es
 push ax
 call far terminal_recording_owned_far
 or ax,ax
 pop ax
 jnz .done
 cmp word [uart_break_hold],0
 jne .done
 cmp word [terminal_controller_active],0
 jne .done
 cmp word [terminal_monitor_active],0
 jne .done
 cmp word [terminal_transfer_pending],0
 jne .done
 cmp word [terminal_transfer_active],0
 jne .done
 cmp word [uart_software_flow],0
 jne .soft
 cmp word [uart_rx_mask],255
 jne .masked
 cmp word [connection_state],0
 je .start
 cmp word [connection_state],6
 jne .done
.start:
 mov [terminal_transfer_direction],ax
 mov word [terminal_transfer_automatic],0
 call terminal_macro_cancel
 call terminal_program_cancel
 mov word [terminal_transfer_pending],1
 mov word [terminal_transfer_grace],0
 jmp .done
.soft:
 mov byte [transfer_note_soft],'R'
 or ax,ax
 jz .soft_note
 mov byte [transfer_note_soft],'T'
.soft_note:
 mov si,transfer_note_soft
 call terminal_connection_notice
 jmp .done
.masked:
 mov si,transfer_note_mask
 call terminal_connection_notice
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

terminal_transfer_poll:
 push bp
 push bx
 push si
 push di
 push es
 cmp word [terminal_transfer_pending],0
 je .done
 call terminal_printer_barrier
 or ax,ax
 jnz .done ;Main polls printer before retry; keep binary transfer out of sink.
 mov word [terminal_transfer_pending],0
 mov word [terminal_transfer_active],1
 mov word [terminal_transfer_phase],0
 mov word [terminal_transfer_fault],0
 mov word [terminal_transfer_cleanup_status],0
 mov word [terminal_transfer_eot_deferred],0
 mov word [terminal_transfer_native_status],0
 mov word [transfer_protocol_started],0
 mov word [transfer_context_active],0
 mov word [transfer_last_blocks],0
 mov word [transfer_carrier_seen],0
 mov word [terminal_upload_blocks_accepted],0
 mov word [terminal_upload_accepted_bytes],0
 mov word [terminal_upload_accepted_bytes+2],0
 mov word [terminal_upload_frame_active],0
 mov word [terminal_upload_cancel_pending],0
 call terminal_transfer_set_budget
 call terminal_connection_notice_restore
 call terminal_clock_ticks
 mov [transfer_progress_tick],ax
 mov [transfer_progress_tick+2],dx
 mov [transfer_wait_tick],ax
 mov [transfer_wait_tick+2],dx
.drain:
 call terminal_transfer_service
 cmp word [terminal_transfer_fault],0
 jne .finish
 cmp word [terminal_tx_count],0
 je .physical
 mov bx,[terminal_tx_head]
 mov al,[terminal_tx_buffer+bx]
 call uart_try_write
 jc .drain_wait
 mov bx,[terminal_tx_head]
 extern terminal_tx_origin_delivered_far
 call far terminal_tx_origin_delivered_far
 mov bx,[terminal_tx_head]
 inc bx
 and bx,1023
 mov [terminal_tx_head],bx
 dec word [terminal_tx_count]
 inc word [terminal_macro_tx_epoch]
 ; A slow line can legitimately drain for longer than36ticks. Bound lack
 ; of UART acceptance, not total queued text duration; never refresh on busy.
 call terminal_clock_ticks
 mov [transfer_wait_tick],ax
 mov [transfer_wait_tick+2],dx
 jmp .drain
.physical:
 mov dx,[uart_port_lsr]
 in al,dx
 and al,0x60
 cmp al,0x60
 je .prompt
.drain_wait:
 mov si,transfer_wait_tick
 call transfer_elapsed
 cmp dx,0
 jne .drain_failed
 cmp ax,36
 jb .drain
.drain_failed:
 mov word [terminal_transfer_fault],6
 jmp .finish
.prompt:
 mov word [terminal_transfer_phase],1
 call terminal_transfer_ui_open
 or ax,ax
 jz .finish
 call terminal_transfer_ui_receiving
 mov word [terminal_transfer_phase],2
 call terminal_clock_ticks
 mov [transfer_progress_tick],ax
 mov [transfer_progress_tick+2],dx
 cmp word [terminal_transfer_protocol],2
 je .zmodem
 cmp word [terminal_transfer_protocol],1
 je .batch
 cmp word [terminal_transfer_direction],1
 jne .receive
 call _terminal_upload_store
 or ax,ax
 jnz .failed
 cmp word [terminal_transfer_fault],0
 jne .failed
 mov si,transfer_note_success
 jmp .notice
.zmodem:
 push word [terminal_transfer_direction]
 call _terminal_zmodem_store
 add sp,2
 jmp .batch_result
.batch:
 call _terminal_batch_store
.batch_result:
 cmp ax,2
 je .batch_unconfirmed
 or ax,ax
 jnz .failed
 cmp word [terminal_transfer_fault],0
 jne .failed
 mov si,transfer_note_success
 jmp .notice
.batch_unconfirmed:
 mov si,transfer_note_batch_ack
 cmp word [terminal_transfer_protocol],2
 jne .unconfirmed_notice
 mov si,transfer_note_zmodem_end
.unconfirmed_notice:
 jmp .notice
.receive:
 call _terminal_transfer_store
 or ax,ax
 jnz .failed
 cmp word [terminal_transfer_fault],0
 jne .failed
 ; The native finalACK was suppressed. Publish it only after exactwrite,
 ; checkedclose and no-overwrite installation have all succeeded.
 mov al,6
 call transfer_emit
 jc .failed
 mov word [terminal_transfer_grace],1
 call terminal_clock_ticks
 mov [transfer_grace_tick],ax
 mov [transfer_grace_tick+2],dx
 mov si,transfer_note_success
 jmp .notice
.failed:
 cmp word [transfer_protocol_started],0
 je .finish
 cmp word [terminal_transfer_protocol],2
 jne .cancel_pair
 ; The live engine's ordinary output callback refuses writes once Escape
 ; latches a fault. Use the bounded fault-tolerant physical writer here.
 ; ZMODEM requires at least five CAN bytes; X/YMODEM's pair is insufficient.
 mov cx,8
.z_cancel:
 mov al,0x18
 call transfer_emit_cancel
 loop .z_cancel
 mov cx,10
.z_backspace:
 mov al,8
 call transfer_emit_cancel
 loop .z_backspace
 call transfer_cancel_drain
 jmp .finish
.cancel_pair:
 ; Best-effort bounded CAN pair; never unwind through a dead native frame.
 mov al,0x18
 call transfer_emit_cancel
 mov al,0x18
 call transfer_emit_cancel
.finish:
 mov si,transfer_note_cancel
 cmp word [terminal_transfer_cleanup_status],0
 jne .recovery_note
 cmp word [terminal_transfer_direction],1
 je .error_note
 cmp word [terminal_transfer_protocol],2
 je .zmodem_saved
 cmp word [terminal_transfer_protocol],1
 jne .ordinary_saved
 cmp word [terminal_transfer_phase],2
 jne .error_note
 mov ax,[_ymodem_current+10] ;DWORD completed files in this batch
 or ax,[_ymodem_current+12]
 jz .error_note
 mov si,transfer_note_batch_partial
 jmp .notice
.zmodem_saved:
 cmp word [terminal_transfer_phase],2
 jne .error_note
 mov ax,[_terminal_zmodem_files]
 or ax,[_terminal_zmodem_files+2]
 jz .error_note
 mov si,transfer_note_batch_partial
 jmp .notice
.ordinary_saved:
 cmp word [_transfer_download_result],3
 jne .error_note
 cmp word [terminal_transfer_fault],0
 je .success_note
 mov si,transfer_note_ack
 jmp .notice
.success_note:
 mov si,transfer_note_success
 jmp .notice
.recovery_note:
 mov si,transfer_note_recovery
 jmp .notice
.error_note:
 mov ax,[terminal_transfer_fault]
 cmp ax,3
 jne .not_timeout
 mov si,transfer_note_timeout
 jmp .notice
.not_timeout:
 cmp ax,4
 jne .not_carrier
 mov si,transfer_note_carrier
 jmp .notice
.not_carrier:
 cmp ax,5
 jne .not_overflow
 mov si,transfer_note_overflow
 jmp .notice
.not_overflow:
 cmp ax,6
 jne .not_stall
 mov si,transfer_note_stall
 jmp .notice
.not_stall:
 cmp ax,7
 jb .notice
 mov si,transfer_note_file
.notice:
 mov byte [si],'R'
 cmp word [terminal_transfer_direction],1
 jne .draw_notice
 mov byte [si],'T'
.draw_notice:
 mov word [terminal_upload_frame_active],0
 mov word [terminal_upload_cancel_pending],0
 mov word [terminal_upload_startup_ansi],0
 call terminal_transfer_ui_restore
 mov word [terminal_transfer_phase],0
 mov word [terminal_transfer_active],0
 mov word [terminal_transfer_automatic],0
 call terminal_connection_notice
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

; AX=elapsed full BIOSdayticks from DS:SI, normalized across midnight.
transfer_elapsed:
 call terminal_clock_ticks
 sub ax,[si]
 sbb dx,[si+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done: ret

; Serviced transfer-only poll. During filename entry the prompt owns BIOS keys.
; No parser/macro/PROGRAM/dial callbacks run while this owner is active.
terminal_transfer_service:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%ifdef TERMINAL_TRAPS
 extern terminal_trap_poll
 call far terminal_trap_poll
%endif
 call uart_poll_flow
 cmp word [terminal_quit],0
 je .rx
 mov ax,2
 jmp .fault
.rx:
 cmp word [uart_rx_dropped],0
 je .carrier
 mov ax,5
 jmp .fault
.carrier:
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x80
 jz .carrier_low
 mov word [transfer_carrier_seen],1
 jmp .clock
.carrier_low:
 cmp word [transfer_carrier_seen],0
 je .clock
 mov ax,4
 jmp .fault
.clock:
 cmp word [terminal_transfer_phase],2
 jne .keys
 mov si,transfer_progress_tick
 call transfer_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,[transfer_progress_budget]
 jb .keys
.timeout:
 mov ax,3
 jmp .fault
.keys:
 cmp word [terminal_transfer_phase],1
 je .done
 call keyboard_poll
 or ax,ax
 jz .done
 call terminal_read_key
 cmp ax,0x2d00
 jne .escape
 mov word [terminal_quit],1
 mov ax,2
 jmp .fault
.escape:
 cmp al,27
 jne .done
 ; Only local Escape in an ordinary sender packet is deferred. Carrier,
 ; overflow, progress deadlines, physical TX bounds and Alt-X stay immediate.
 cmp word [terminal_upload_frame_active],0
 je .cancel_now
 mov word [terminal_upload_cancel_pending],1
 jmp .done
.cancel_now:
 mov ax,2
.fault:
 cmp word [terminal_transfer_fault],0
 jne .done
 mov [terminal_transfer_fault],ax
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret

; Fail from a foreground callback only. Context is established BEFORE the native
; handshake, so CTS/cancel/deadline failures cannot jump through an empty context.
transfer_maybe_unwind:
 cmp word [terminal_transfer_fault],0
 je .done
 cmp word [transfer_context_active],0
 je .done
 mov ax,1
 push ax
 mov ax,transfer_outer_context
 push ax
 call session_longjmp
.done: ret
GLOBAL _terminal_transfer_native_call
_terminal_transfer_native_call:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,transfer_outer_context
 push ax
 call session_setjmp
 add sp,2
 or ax,ax
 jnz .unwound
 mov word [transfer_context_active],1
 push word [bp+4]
 cmp word [terminal_transfer_direction],1
 je .send
 call _terminal_transfer_receive
 jmp .returned
.send:
 call _terminal_transfer_send
.returned:
 add sp,2
 mov word [transfer_context_active],0
 jmp .done
.unwound:
 mov word [transfer_context_active],0
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

; AL raw byte, CF busy/failure.36tick physical/flow stall bound perbyte.
transfer_emit:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov bl,al
 call terminal_clock_ticks
 mov [transfer_tx_tick],ax
 mov [transfer_tx_tick+2],dx
.wait:
 call terminal_transfer_service
 cmp word [terminal_transfer_fault],0
 jne .failed
 mov al,bl
 call uart_try_write
 jnc .success
 mov si,transfer_tx_tick
 call transfer_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jb .wait
.timeout:
 mov word [terminal_transfer_fault],6
.failed:
 stc
 jmp .done
.success:
 clc
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret

; Cancellation control does not mistake the already-latched failure for a new
; send failure. No parser or DOS calls, finite36ticks even when CTS/THRE stall.
transfer_emit_cancel:
 push ax
 push bx
 push dx
 push si
 mov bl,al
 call terminal_clock_ticks
 mov [transfer_tx_tick],ax
 mov [transfer_tx_tick+2],dx
.wait:
 call uart_poll_flow
 mov al,bl
 call uart_try_write
 jnc .done
 mov si,transfer_tx_tick
 call transfer_elapsed
 or dx,dx
 jnz .done
 cmp ax,36
 jb .wait
.done:
 pop si
 pop dx
 pop bx
 pop ax
 ret

; Keep canceled binary data away from the ANSI parser while the peer stops.
; Nine quiet BIOS ticks tolerate delayed serial/modem delivery;180 total ticks
; bound a peer that never stops. Real receive consumption retains
; the UART driver's RTS/low-water policy; no parser or DOS callbacks run here.
transfer_cancel_drain:
 push ax
 push dx
 push si
 call terminal_clock_ticks
 mov [transfer_wait_tick],ax
 mov [transfer_wait_tick+2],dx
 mov [transfer_delay_tick],ax
 mov [transfer_delay_tick+2],dx
.wait:
 call uart_poll_flow
 cmp word [uart_rx_count],0
 je .bounds
 call terminal_transfer_flush_input
 call terminal_clock_ticks
 mov [transfer_delay_tick],ax
 mov [transfer_delay_tick+2],dx
.bounds:
 mov si,transfer_wait_tick
 call transfer_elapsed
 or dx,dx
 jnz .stalled
 cmp ax,180
 jb .quiet
.stalled:
 ; Returning an active binary stream to ANSI parsing is unsafe. Leave the
 ; session with the existing ownership-failure exit rather than resume it.
 mov word [terminal_quit],1
 mov word [terminal_exit_code],14
 jmp .done
.quiet:
 mov si,transfer_delay_tick
 call transfer_elapsed
 or dx,dx
 jnz .stalled
 cmp ax,9
 jb .wait
.done:
 pop si
 pop dx
 pop ax
 ret

GLOBAL terminal_transfer_transmit_byte
terminal_transfer_transmit_byte:
 ; Native BP remains its58h-frame here (receive_ack does not changeBP).
 cmp word [ss:bp-0x10],4
 jne .emit
 mov bx,sp
 cmp word [ss:bx+2],6
 jne .emit
 mov word [terminal_transfer_eot_deferred],1
 ret 2
.emit:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 call transfer_emit
 jc .failed
 mov word [transfer_protocol_started],1
.failed:
 call transfer_maybe_unwind
 pop bp
 ret 2

GLOBAL terminal_transfer_timed_byte,terminal_transfer_header_byte
terminal_transfer_header_byte:
 mov ax,2
 push ax
 call terminal_transfer_timed_byte
 ret
terminal_transfer_timed_byte:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov bx,[bp+4]
 cmp bx,30
 jbe .bounded
 mov bx,30
.bounded:
 mov ax,19
 mul bx
 mov di,ax ;conservative bounded BIOS ticks per requested second
 call terminal_clock_ticks
 mov [transfer_read_tick],ax
 mov [transfer_read_tick+2],dx
.wait:
 call terminal_transfer_service
 call transfer_maybe_unwind
 cmp word [terminal_transfer_fault],0
 jne .timeout
 call uart_receive_byte
 cmp ax,0xffff
 jne .done
 mov si,transfer_read_tick
 call transfer_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,di
 jb .wait
.timeout:
 mov ax,0xffff
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret 2

GLOBAL terminal_transfer_delay_ticks,terminal_transfer_delay_legacy
terminal_transfer_delay_ticks:
 push bp
 mov bp,sp
 push ax
 mov ax,[bp+4]
 cmp ax,10
 jbe .bounded
 mov ax,10
.bounded:
 inc ax ;explicit native BIOS tick-change wait: argument+1
 call transfer_delay
 pop ax
 pop bp
 ret 2
terminal_transfer_delay_legacy:
 push ax
 mov ax,2 ;maintained two-BIOS-tick quiet interval, NOT calibrated units
 call transfer_delay
 pop ax
 ret 2
transfer_delay:
 push bx
 push cx
 push dx
 push si
 push di
 mov di,ax
 call terminal_clock_ticks
 mov [transfer_delay_tick],ax
 mov [transfer_delay_tick+2],dx
.wait:
 call terminal_transfer_service
 call transfer_maybe_unwind
 mov si,transfer_delay_tick
 call transfer_elapsed
 or dx,dx
 jnz .done
 cmp ax,di
 jb .wait
.done:
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret

GLOBAL terminal_transfer_flush_input
terminal_transfer_flush_input:
 push ax
 push cx
 mov cx,[uart_rx_count] ;discard only the bounded snapshot, not future arrivals
.next:
 jcxz .done
 call uart_receive_byte ;real lowwater/RTS ownership maintained by driver
 loop .next
.done:
 pop cx
 pop ax
 ret
GLOBAL terminal_transfer_local_cancel,terminal_transfer_carrier_present
terminal_transfer_local_cancel:
 call terminal_transfer_service
 call transfer_maybe_unwind
 mov ax,[terminal_transfer_fault]
 ret
terminal_transfer_carrier_present:
 call terminal_transfer_service
 call transfer_maybe_unwind
 mov ax,1
 cmp word [terminal_transfer_fault],0
 je .done
 xor ax,ax
.done: ret
GLOBAL terminal_transfer_progress,terminal_transfer_status,terminal_transfer_clock
terminal_transfer_progress:
 push ax
 push dx
 mov ax,[session_blocks_accepted]
 cmp ax,[transfer_last_blocks]
 je .draw
 mov [transfer_last_blocks],ax
 call terminal_clock_ticks
 mov [transfer_progress_tick],ax
 mov [transfer_progress_tick+2],dx
.draw:
 call terminal_transfer_ui_progress
 call terminal_transfer_service
 call transfer_maybe_unwind
 pop dx
 pop ax
 ret
terminal_transfer_status:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [terminal_transfer_native_status],ax
 pop bp
 ret
terminal_transfer_clock: jmp terminal_clock_ticks
; An actual accepted block, never a legacy attempted-block counter.
terminal_transfer_accepted_progress:
 push ax
 push dx
 call terminal_clock_ticks
 mov [transfer_progress_tick],ax
 mov [transfer_progress_tick+2],dx
 pop dx
 pop ax
 ret

GLOBAL terminal_transfer_file_open,terminal_transfer_file_write,terminal_transfer_file_close
terminal_transfer_file_open: jmp _transfer_native_open
terminal_transfer_file_write: jmp _transfer_native_write
terminal_transfer_file_close: jmp _transfer_native_close
GLOBAL terminal_transfer_path_test,terminal_transfer_display_path
terminal_transfer_path_test:
 xor ax,ax ;validated explicit stage path, no native prefix search
 ret
terminal_transfer_display_path:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 pop bp
 ret
GLOBAL terminal_transfer_ui_print,terminal_transfer_setflow,terminal_transfer_timestamp
terminal_transfer_ui_print:
 call terminal_transfer_ui_progress ;native labels reflected by live receive UI
 ret 6
terminal_transfer_setflow:
 call uart_poll_flow ;nativegateis0 here; ISRownsactualHARDwatermarks
 ret
terminal_transfer_timestamp:
 xor ax,ax ;ordinaryXMODEM has no remote timestamp; keep DOScreated timestamp
 ret
GLOBAL terminal_transfer_unsupported
terminal_transfer_unsupported:
 mov word [terminal_transfer_fault],10
 call transfer_maybe_unwind
 ; No unsupported protocol may silently return success.
 extern terminal_abort
 mov ax,0xfa08
 jmp terminal_abort

; Main's post-session input filter. Retransmitted EOT receives ACK for10seconds
; until first non-EOT application byte; no file IO or reinstall happens here.
terminal_transfer_filter:
 push ax
 push bx
 push dx
 push si
 cmp word [terminal_transfer_grace],0
 je .pass
 mov bx,ax
 mov si,transfer_grace_tick
 call transfer_elapsed
 or dx,dx
 jnz .expire
 cmp ax,190
 jae .expire
 cmp bx,4
 jne .expire
 mov al,6
 extern terminal_enqueue_al
 call terminal_enqueue_al
 pop si
 pop dx
 pop bx
 pop ax
 stc
 ret
.expire:
 mov word [terminal_transfer_grace],0
.pass:
 pop si
 pop dx
 pop bx
 pop ax
 clc
 ret
; Accepted-progress deadline, not an idle-byte timer. ZedZap can contain8192
; payload bytes plus quoting before a verified packet exists. Allow the worst
; quoted packet on a slow UART without treating unverified bytes as progress.
; A connected modem's DTE baud is not a carrier-speed lower bound. The legacy
; first-completion CONNECT matcher supplies no reliable DCE rate, so cover the
; supported300bps floor for that context. Direct-directory/raw serial sessions
; retain their UART-based budget. Per-read idle/retry and physical TX/flow stall
; bounds remain independent; unverified input never refreshes this deadline.
GLOBAL terminal_transfer_set_budget,transfer_progress_budget
terminal_transfer_set_budget:
 cmp word [connection_state],6
 jne .uart_rate
 cmp word [terminal_directory_mode],1
 je .uart_rate
 mov word [transfer_progress_budget],2160
 cmp word [terminal_transfer_protocol],2
 jne .done
 mov word [transfer_progress_budget],17280
 ret
.uart_rate:
 mov word [transfer_progress_budget],540
 cmp word [terminal_baud_high],0
 jne .done
 cmp word [terminal_transfer_protocol],2
 je .zmodem
 cmp word [terminal_baud_low],1200
 jae .done
 mov word [transfer_progress_budget],2160
 ret
.zmodem:
 cmp word [terminal_baud_low],9600
 jae .done
 mov word [transfer_progress_budget],1080
 cmp word [terminal_baud_low],4800
 jae .done
 mov word [transfer_progress_budget],2160
 cmp word [terminal_baud_low],2400
 jae .done
 mov word [transfer_progress_budget],4320
 cmp word [terminal_baud_low],1200
 jae .done
 mov word [transfer_progress_budget],8640
 cmp word [terminal_baud_low],600
 jae .done
 mov word [transfer_progress_budget],17280
.done:
 ret
terminal_transfer_shutdown:
 call _terminal_transfer_cleanup
 push ax
 call _terminal_upload_cleanup
 pop bx
 or ax,bx
 or ax,ax
 jz .done
 cmp word [terminal_exit_code],0
 jne .done
 mov word [terminal_exit_code],12
.done: ret
SEGMENT _DATA public class=DATA use16
GLOBAL terminal_transfer_pending,terminal_transfer_active,terminal_transfer_fault
GLOBAL _terminal_transfer_fault,terminal_transfer_cleanup_status,_terminal_transfer_cleanup_status
GLOBAL terminal_transfer_eot_deferred,_terminal_transfer_eot_deferred
GLOBAL terminal_transfer_native_status,_terminal_transfer_native_status
GLOBAL terminal_transfer_filename,_terminal_transfer_filename
GLOBAL terminal_transfer_protocol,_terminal_transfer_protocol,_terminal_transfer_direction
GLOBAL terminal_transfer_automatic
terminal_transfer_automatic: dw 0
terminal_transfer_pending: dw 0
terminal_transfer_active: dw 0
_terminal_transfer_direction:
terminal_transfer_direction: dw 0
_terminal_transfer_protocol:
terminal_transfer_protocol: dw 0 ;0ordinary XMODEM,1CRC YMODEM,2ZMODEM
terminal_transfer_phase: dw 0
_terminal_transfer_fault:
terminal_transfer_fault: dw 0
_terminal_transfer_cleanup_status:
terminal_transfer_cleanup_status: dw 0
_terminal_transfer_eot_deferred:
terminal_transfer_eot_deferred: dw 0
_terminal_transfer_native_status:
terminal_transfer_native_status: dw 0
_terminal_transfer_filename:
terminal_transfer_filename: times 64 db 0
terminal_transfer_grace: dw 0
transfer_grace_tick: dd 0
transfer_progress_tick: dd 0
transfer_wait_tick: dd 0
transfer_tx_tick: dd 0
transfer_read_tick: dd 0
transfer_delay_tick: dd 0
transfer_progress_budget: dw 540
transfer_last_blocks: dw 0
transfer_carrier_seen: dw 0
transfer_context_active: dw 0
transfer_outer_context: times 10 db 0
transfer_protocol_started: dw 0
transfer_note_success: db 'RX complete',0
transfer_note_cancel: db 'RX canceled',0
transfer_note_soft: db 'RX: HARD/NONE',0
transfer_note_mask: db 'Binary transfer needs an 8-bit input mask. Change settings and restart.',0
transfer_note_timeout: db 'RX timeout',0
transfer_note_carrier: db 'RX carrier lost',0
transfer_note_overflow: db 'RX overflow',0
transfer_note_stall: db 'RX TX stalled',0
transfer_note_file: db 'RX file error',0
transfer_note_recovery: db 'RX recovery!',0
transfer_note_ack: db 'RX saved; ACK?',0
transfer_note_batch_ack: db 'TX batch sent; ACK?',0
transfer_note_zmodem_end: db 'RX files saved; finish unconfirmed',0
transfer_note_batch_partial: db 'RX batch partial',0
