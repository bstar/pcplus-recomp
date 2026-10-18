; Maintained dedicated PRN owner. Native D0D0 remains an exact diagnostic.
; Every callback is bounded. The serviced modal wrapper preserves CSI order.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _printer_device_begin,_printer_device_close,_printer_device_result
extern terminal_printer_poll,terminal_printer_put_raw,terminal_printer_failure
extern terminal_printer_count,terminal_printer_closing,terminal_printer_fault_epoch
extern terminal_sink_3988_enabled,terminal_clock_ticks,terminal_poll_io
extern terminal_quit,terminal_exit_code,terminal_tx_count,uart_rx_dropped
extern terminal_capture_poll
extern uart_receive_byte,uart_poll_flow,uart_port_msr
extern terminal_connection_notice,terminal_connection_notice_restore
extern keyboard_classify_raw,terminal_enqueue_key_slot,terminal_enqueue_al
extern terminal_monitor_active,terminal_snapshot_active,terminal_screen_print_active
extern terminal_transfer_pending,terminal_transfer_active
extern terminal_program_pending,terminal_program_active,terminal_macro_active
extern terminal_ansi_wait_active,connection_state
extern text_cga_status_port,text_video_segment,screen_viewport_enabled
extern terminal_input_mode_8fe8,render_linefeed_suppression_enabled,csi_terminal_id
global terminal_controller_start,terminal_controller_run,terminal_controller_key
global terminal_controller_filter,terminal_controller_poll
global terminal_controller_receive_hold,terminal_controller_shutdown
%macro save 0
 push bp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 ret
%endmacro

terminal_controller_start:
 save
 cmp word [terminal_controller_active],0
 jne .done
 mov word [terminal_controller_last_action],3
 cmp word [text_cga_status_port],0
 jne .done
 cmp word [text_video_segment],0xb800
 jne .done
 cmp word [screen_viewport_enabled],0
 jne .done
 mov ah,0x0f
 int 0x10
 cmp ax,0x5003
 jne .done
 or bh,bh
 jnz .done
 cmp word [terminal_monitor_active],0
 jne .done
 cmp word [terminal_snapshot_active],0
 jne .done
 cmp word [terminal_screen_print_active],0
 jne .done
 cmp word [terminal_transfer_pending],0
 jne .done
 cmp word [terminal_transfer_active],0
 jne .done
 cmp word [terminal_program_pending],0
 jne .done
 cmp word [terminal_program_active],0
 jne .done
 cmp word [terminal_macro_active],0
 jne .done
 cmp word [terminal_ansi_wait_active],0
 jne .done
 cmp word [_printer_device_result+12],0
 jne .done
 cmp word [connection_state],0
 je .admit
 cmp word [connection_state],6
 jne .done
.admit:
 ; Connection polling can observe a falling DCD before this owner's first
 ; poll. Retain the connected state independently of our physical-DCD latch.
 mov ax,[connection_state]
 mov [controller_entry_connection],ax
 mov ax,[terminal_printer_fault_epoch]
 mov [controller_epoch],ax
 mov ax,[terminal_sink_3988_enabled]
 mov [controller_saved_copy],ax
 mov word [controller_temporary],0
 mov word [controller_acquired],0
 mov word [controller_last_escape],0
 mov word [controller_replay_on_stop],0
 mov word [controller_carrier_seen],0
 call controller_reset_prefix
 call terminal_connection_notice_restore
 mov ah,3
 xor bh,bh
 int 0x10
 mov [controller_cursor_shape],cx
 mov word [terminal_controller_active],3
 mov word [terminal_controller_last_action],1
 mov word [terminal_sink_3988_enabled],0
 cmp word [terminal_printer_closing],0
 jne .notice
 call controller_acquire
 cmp word [terminal_controller_active],0
 je .done
.notice:
 mov si,controller_notice
 call terminal_connection_notice
.done:
 restore

controller_acquire:
 cmp word [_printer_device_result+10],0
 jne .opened
 call _printer_device_begin
 or ax,ax
 jz .temporary
 cmp ax,5
 je .denied
 call terminal_printer_failure
 jmp controller_failed
.denied:
 mov word [terminal_controller_last_action],3
 jmp controller_release
.temporary:
 mov word [controller_temporary],1
.opened:
 mov word [controller_acquired],1
 mov word [terminal_controller_active],1
 ret

terminal_controller_run:
 save
 call terminal_controller_start
.loop:
 cmp word [terminal_controller_active],0
 je .done
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne .shutdown
 call terminal_capture_poll
 call terminal_printer_poll
 call terminal_controller_poll
 cmp word [terminal_quit],0
 jne .shutdown
 cmp word [terminal_controller_active],0
 je .done
 call terminal_controller_receive_hold
 or ax,ax
 jnz .idle
 call uart_receive_byte
 cmp ax,0xffff
 je .idle
 call terminal_controller_filter
 jmp .loop
.idle:
 cmp word [terminal_tx_count],0
 jne .loop
 sti
 hlt
 jmp .loop
.shutdown:
 call terminal_controller_shutdown
.done:
 restore

terminal_controller_receive_hold:
 xor ax,ax
 cmp word [terminal_controller_active],0
 je .done
 cmp word [terminal_controller_active],1
 jne .hold
 cmp word [terminal_printer_count],95
 jbe .done
.hold:
 inc ax
.done: ret

; AX is an actual dequeued byte. Never invent an EOF/sentinel byte.
terminal_controller_filter:
 save
 cmp word [terminal_controller_active],0
 je .normal
 cmp word [terminal_controller_active],1
 jne .consumed ;Callers must honor receive_hold before dequeue.
 and ax,255
 or ax,ax
 jz .consumed
 cmp ax,127
 je .consumed
 mov bx,[terminal_controller_buffer_count]
 or bx,bx
 jnz .buffered
 cmp ax,20
 jne .escape
 cmp word [csi_terminal_id],31
 je .wire_stop
 ; Deliberate fix: native prints this ordinary byte twice. Print it once.
.escape:
 cmp ax,27
 jne .literal
 mov byte [controller_buffer],27
 mov word [terminal_controller_buffer_count],1
 call terminal_clock_ticks
 mov [controller_prefix_tick],ax
 mov [controller_prefix_tick+2],dx
 jmp .consumed
.literal:
 call controller_put
 jmp .consumed
.buffered:
 cmp bx,32
 jb .append
 ; Reserve33 queue slots in receive_hold. Replay the bounded prefix and
 ; current byte literally, once, then restart only on a later byte.
 push ax
 call controller_replay
 pop ax
 call controller_put
 jmp .consumed
.append:
 mov [controller_buffer+bx],al
 inc word [terminal_controller_buffer_count]
 cmp word [terminal_input_mode_8fe8],0
 je .special
 cmp al,'0'
 jb .special
 cmp al,'9'
 ja .special
 cmp al,'4'
 jne .consumed
 mov word [controller_saw_four],1
 jmp .consumed
.special:
 cmp al,';'
 je .consumed
 cmp al,'['
 je .bracket
 cmp al,'i'
 je .final_i
 cmp al,'X'
 je .profile_one
 cmp al,'a'
 je .other_profile
 call controller_replay
 jmp .consumed
.bracket:
 cmp word [terminal_input_mode_8fe8],0
 je .consumed
 mov word [controller_saw_bracket],1
 jmp .consumed
.final_i:
 cmp word [terminal_input_mode_8fe8],0
 je .consumed
 cmp word [controller_saw_bracket],0
 je .consumed
 cmp word [controller_saw_four],0
 jne .wire_stop
 call controller_reset_prefix ;Native suppresses bracket+i without digit4.
 jmp .consumed
.profile_one:
 cmp word [csi_terminal_id],1
 jne .consumed
 jmp .previous_escape
.other_profile:
 cmp word [render_linefeed_suppression_enabled],0
 je .consumed
.previous_escape:
 cmp byte [controller_buffer+bx-1],27
 jne .consumed
.wire_stop:
 call controller_reset_prefix
 mov word [terminal_controller_last_action],2
 mov word [terminal_controller_active],2
.consumed:
 stc
 restore
.normal:
 clc
 restore

controller_put:
 push ax
 call terminal_printer_put_raw
 add sp,2
 ret
controller_reset_prefix:
 mov word [terminal_controller_buffer_count],0
 mov word [controller_saw_bracket],0
 mov word [controller_saw_four],0
 ret
controller_replay:
 xor si,si
.byte:
 cmp si,[terminal_controller_buffer_count]
 jae .done
 xor ax,ax
 mov al,[controller_buffer+si]
 call controller_put
 inc si
 jmp .byte
.done:
 jmp controller_reset_prefix

terminal_controller_poll:
 save
 cmp word [terminal_controller_active],0
 je .done
 mov ax,[terminal_printer_fault_epoch]
 cmp ax,[controller_epoch]
 jne .failed
 cmp word [uart_rx_dropped],0
 je .carrier
 mov word [terminal_exit_code],6
 mov word [terminal_quit],1
.carrier:
 cmp word [controller_entry_connection],6
 jne .physical_carrier
 cmp word [connection_state],6
 je .physical_carrier
 call controller_cancel
.physical_carrier:
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x80
 jz .carrier_low
 mov word [controller_carrier_seen],1
 jmp .state
.carrier_low:
 cmp word [controller_carrier_seen],0
 je .state
 call controller_cancel
.state:
 cmp word [terminal_controller_active],3
 jne .owner
 cmp word [terminal_printer_closing],0
 jne .done
 call controller_acquire
 jmp .done
.owner:
 cmp word [controller_acquired],0
 jne .owned
 cmp word [terminal_printer_closing],0
 jne .done
 jmp .release
.owned:
 cmp word [_printer_device_result+10],0
 jne .present
 mov ax,4
 call terminal_printer_failure
 jmp .failed
.present:
 cmp word [terminal_controller_active],2
 je .draining
 cmp word [terminal_controller_buffer_count],0
 je .done
 mov si,controller_prefix_tick
 call controller_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jb .done
.timeout:
 cmp word [terminal_printer_count],95
 ja .done
 call controller_replay
 jmp .done
.draining:
 cmp word [controller_replay_on_stop],0
 je .queue
 cmp word [terminal_printer_count],95
 ja .done
 call controller_replay
 mov word [controller_replay_on_stop],0
.queue:
 cmp word [terminal_printer_count],0
 jne .done
 cmp word [controller_temporary],0
 je .release
 call _printer_device_close
 or ax,ax
 jz .release
 call terminal_printer_failure
.failed:
 call controller_failed
 jmp .done
.release:
 call controller_release
.done:
 restore

controller_cancel:
 cmp word [terminal_controller_active],0
 je .done
 mov word [terminal_controller_active],2
 mov word [terminal_controller_last_action],5
 mov word [controller_replay_on_stop],1
.done: ret
controller_failed:
 mov word [terminal_controller_last_action],4
 mov word [controller_saved_copy],0
 call controller_reset_prefix
controller_release:
 mov ax,[controller_saved_copy]
 mov [terminal_sink_3988_enabled],ax
 mov word [terminal_controller_active],0
 mov word [controller_replay_on_stop],0
 call controller_reset_prefix
 mov cx,[controller_cursor_shape]
 mov ah,1
 int 0x10
 call terminal_connection_notice_restore
 ret

; Consume nested local/KEY owners; normal literals/network slots retain TX.
terminal_controller_key:
 save
 cmp word [terminal_controller_active],0
 je .normal
 cmp ax,0x2d00
 je .leave_normal
 cmp ax,0x2300
 je .leave_normal
 cmp al,0x1c
 je .consumed
 cmp al,27
 jne .other
 cmp word [controller_last_escape],0
 jne .cancel
 mov word [controller_last_escape],1
 cmp word [terminal_controller_active],1
 jne .consumed
 call terminal_enqueue_al ;BIOS011B and normalized001B both mean literalESC.
 jmp .consumed
.other:
 mov word [controller_last_escape],0
.transmit:
 cmp word [terminal_controller_active],1
 jne .consumed
 call keyboard_classify_raw
 cmp ax,79
 jb .binding
 cmp ah,1
 jne .consumed
 call terminal_enqueue_al
 jmp .consumed
.binding:
 call terminal_enqueue_key_slot
 jmp .consumed
.cancel:
 call controller_cancel
.consumed:
 stc
 restore
.leave_normal:
 call controller_cancel
.normal:
 clc
 restore

controller_elapsed:
 call terminal_clock_ticks
 sub ax,[si]
 sbb dx,[si+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done: ret

; Shutdown is bounded independently of per-byte progress. No device close is
; retried after an uncertain outcome. The caller subsequently shuts PRN down.
terminal_controller_shutdown:
 save
 cmp word [terminal_controller_active],0
 je .done
 call controller_cancel
 call terminal_clock_ticks
 mov [controller_shutdown_tick],ax
 mov [controller_shutdown_tick+2],dx
.drain:
 call uart_poll_flow
 call terminal_printer_poll
 call terminal_controller_poll
 cmp word [terminal_controller_active],0
 je .done
 mov si,controller_shutdown_tick
 call controller_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jb .drain
.timeout:
 mov ax,14
 call terminal_printer_failure
 call controller_failed
.done:
 restore

SEGMENT _DATA public class=DATA use16
global terminal_controller_active,terminal_controller_last_action
global terminal_controller_buffer_count
terminal_controller_active: dw 0 ;0off,1raw,2drain,3prior-close admission
terminal_controller_last_action: dw 0 ;1entered,2wire exit,3denied,4fault,5cancel
terminal_controller_buffer_count: dw 0
controller_saved_copy: dw 0
controller_temporary: dw 0
controller_acquired: dw 0
controller_last_escape: dw 0
controller_replay_on_stop: dw 0
controller_carrier_seen: dw 0
controller_entry_connection: dw 0
controller_cursor_shape: dw 0
controller_epoch: dw 0
controller_saw_four: dw 0
controller_saw_bracket: dw 0
controller_prefix_tick: dd 0
controller_shutdown_tick: dd 0
controller_buffer: times 32 db 0
controller_notice: db 'Dedicated PRN',0
