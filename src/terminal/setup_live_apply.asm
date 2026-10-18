; Live settings owner over CONFIG_CODE. DS=SS. All file/native validation
; precedes global application; transport/profile/directory remain owned by the
; existing session. No screen repaint or transport reset is performed here.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS
%include "terminal_import.inc"
%include "modem_import.inc"
%include "directory_live.inc"
SEGMENT _TEXT public class=CODE use16
extern _live_setup_bind,_live_setup_begin,_live_setup_finish,_live_setup_abort
extern _live_setup_finish_policy,_live_setup_acknowledge
extern terminal_config_path,terminal_option_mask,terminal_directory_context
extern terminal_directory_context_valid,terminal_configuration_values
extern terminal_modem_settings,terminal_directory_plan,terminal_dial_target
extern terminal_port_number,terminal_baud_low,terminal_baud_high
extern terminal_parity,terminal_data_bits,terminal_stop_bits,terminal_break_delay_units
extern uart_software_flow,uart_hardware_flow,uart_port_rbr,uart_irq_indices
extern uart_tx_paused,uart_xoff_sent,uart_flow_pending,uart_rts_lowered,uart_rx_count
extern terminal_program_prepare_link
extern terminal_connection_prepare,terminal_apply_live_configuration
extern terminal_program_status,terminal_exit_code,terminal_quit
global terminal_setup_bind,terminal_setup_prepare,terminal_setup_complete
global terminal_setup_return_prompt
%macro save 0
 push bp
 push si
 push di
 push es
 push ds
 pop es
 cld
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop bp
 ret
%endmacro
terminal_setup_bind:
 save
 mov word [terminal_setup_binding_status],2
 test word [terminal_option_mask],16
 jz .done
 mov ax,terminal_configuration_values
 push ax
 call setup_context_pointer
 push ax
 mov ax,terminal_config_path
 push ax
 call _live_setup_bind
 add sp,6
 mov [terminal_setup_binding_status],ax
.done:
 restore
setup_context_pointer:
 xor ax,ax
 cmp word [terminal_directory_context_valid],1
 jne .done
 mov ax,terminal_directory_context
.done:
 ret

; Called after the foreground owner has quiesced UART/IRQ, immediately before
; direct EXEC. The plan combines configured display policy with ACTUAL current
; transport (including negotiated autobaud). The ISR never owns these globals.
terminal_setup_prepare:
 save
 mov word [terminal_setup_apply_status],0
 mov word [terminal_setup_link_status],0
 mov word [terminal_setup_key_consumed],0
 mov word [terminal_setup_outcome],0
 mov word [terminal_setup_outcome+2],0
 mov word [terminal_setup_outcome+4],0
 mov word [terminal_setup_outcome+6],0
 mov si,terminal_configuration_values
 mov di,terminal_setup_plan
 mov cx,TI_SIZE/2
 rep movsw
 %macro actual 2
 mov ax,[%2]
 mov [terminal_setup_plan+%1],ax
 %endmacro
 actual TI_PORT,terminal_port_number
 actual TI_BAUD_LOW,terminal_baud_low
 actual TI_BAUD_HIGH,terminal_baud_high
 actual TI_PARITY,terminal_parity
 actual TI_DATA,terminal_data_bits
 actual TI_STOP,terminal_stop_bits
 actual TI_SOFT,uart_software_flow
 actual TI_HARD,uart_hardware_flow
 actual TI_IO_BASE,uart_port_rbr
 actual TI_IRQ,uart_irq_indices
 mov si,terminal_modem_settings
 mov cx,MI_SIZE/2
 rep movsw
 mov ax,[terminal_break_delay_units]
 mov [terminal_setup_plan+TI_SIZE+MI_BREAK_DELAY],ax
 mov si,terminal_directory_plan
 mov cx,DL_SIZE/2
 rep movsw
 xor ax,ax
 stosw ;624-byte plan ends in the change mask.
 mov ax,terminal_dial_target
 push ax
 push word [terminal_option_mask]
 mov ax,terminal_setup_plan
 push ax
 call setup_context_pointer
 push ax
 mov ax,terminal_config_path
 push ax
 call _live_setup_begin
 add sp,10
 mov [terminal_setup_apply_status],ax
 restore

; Child failure never reloads/adopts the on-disk file. Successful children may
; still produce invalid/unreadable settings; the existing session stays intact.
terminal_setup_complete:
 save
 cmp word [terminal_program_status],4
 je .finish
 xor ax,ax
 push ax
 call _live_setup_abort
 add sp,2
 jmp .done
.finish:
 mov si,terminal_setup_plan
 mov di,setup_previous_serial
 mov cx,TI_SIZE/2
 rep movsw
 mov ax,14
 push ax
 mov ax,terminal_setup_outcome
 push ax
 mov ax,terminal_setup_plan
 push ax
 call _live_setup_finish_policy
 add sp,6
 mov [terminal_setup_apply_status],ax
 or ax,ax
 jnz .done
 call setup_serial_choice
 test word [terminal_setup_outcome+4],128|14
 jz .apply
 ; Prepare future dial/hangup commands only after native expansion validation.
 ; An unexpected prepare failure restores the old settings/commands before
 ; reporting failure. No bytes are sent and connection state is unchanged.
 mov si,terminal_modem_settings
 mov di,setup_previous_modem
 mov cx,MI_SIZE/2
 rep movsw
 test word [terminal_setup_outcome+4],128
 jz .serial_globals
 mov si,terminal_setup_plan+TI_SIZE
 mov di,terminal_modem_settings
 mov cx,MI_SIZE/2
 rep movsw
.serial_globals:
 test word [terminal_setup_outcome+4],14
 jz .prepare_modem
 mov si,terminal_setup_plan
 call setup_install_serial
.prepare_modem:
 call terminal_connection_prepare
 jnc .serial_ready
 push ds
 pop es
 mov si,setup_previous_modem
 mov di,terminal_modem_settings
 mov cx,MI_SIZE/2
 cld
 rep movsw
 mov si,setup_previous_serial
 call setup_install_serial
 call setup_defer_serial
 mov word [terminal_setup_link_status],3
 call terminal_connection_prepare
 jnc .failed
 mov word [terminal_exit_code],7
 mov word [terminal_quit],1 ;Cannot continue with unprepared active commands.
.failed:
 mov word [terminal_setup_apply_status],6
 mov word [terminal_setup_outcome],6
 mov word [terminal_setup_outcome+4],0
 jmp .done
.serial_ready:
 test word [terminal_setup_outcome+4],14
 jz .apply
 call setup_reconcile_flow
.apply:
 push ds
 pop es
 cld
 test word [terminal_setup_outcome+4],512
 jz .display
 mov ax,[terminal_setup_plan+TI_SIZE+MI_BREAK_DELAY]
 mov [terminal_modem_settings+MI_BREAK_DELAY],ax
 mov [terminal_break_delay_units],ax
.display:
 mov ax,terminal_setup_plan
 call terminal_apply_live_configuration
 mov ax,[terminal_setup_outcome+4]
 and ax,2
 push ax
 call _live_setup_acknowledge
 add sp,2
.done:
 restore

setup_serial_choice:
 test word [terminal_setup_outcome+4],14
 jz .done
 mov si,setup_serial_question
.text:
 lodsb
 or al,al
 jz .key
 mov ah,0x0e
 xor bh,bh
 mov bl,7
 int 0x10
 jmp .text
.key:
 xor ax,ax
 int 0x16
 mov word [terminal_setup_key_consumed],1
 cmp al,'Y'
 je .accept
 cmp al,'y'
 je .accept
 mov word [terminal_setup_link_status],2
 call setup_defer_serial
 ret
.accept:
 call terminal_program_prepare_link
 or ax,ax
 jnz .busy
 mov word [terminal_setup_link_status],1
 ret
.busy:
 call setup_defer_serial
 mov word [terminal_setup_link_status],3
 mov word [terminal_setup_key_consumed],0 ;Keep the busy result visible.
.done:
 ret
setup_defer_serial:
 mov ax,[terminal_setup_outcome+4]
 and ax,14
 or [terminal_setup_outcome+6],ax
 and word [terminal_setup_outcome+4],~14
 push si
 push di
 push cx
 push ds
 pop es
 mov si,setup_previous_serial
 mov di,terminal_setup_plan
 mov cx,8 ;Port/baud/line/flow words; profile was already deferred.
 cld
 rep movsw
 pop cx
 pop di
 pop si
 ret
setup_install_serial:
 ; SI validated same-port serial plan; no I/O or baseline capture here.
 mov ax,[si+TI_BAUD_LOW]
 mov [terminal_baud_low],ax
 mov ax,[si+TI_BAUD_HIGH]
 mov [terminal_baud_high],ax
 mov ax,[si+TI_PARITY]
 mov [terminal_parity],ax
 mov ax,[si+TI_DATA]
 mov [terminal_data_bits],ax
 mov ax,[si+TI_STOP]
 mov [terminal_stop_bits],ax
 mov ax,[si+TI_SOFT]
 mov [uart_software_flow],ax
 mov ax,[si+TI_HARD]
 mov [uart_hardware_flow],ax
 ret
setup_reconcile_flow:
 ; The old software pause was physically released at the old format. Carry
 ; peer XOFF only across an already enabled software-flow protocol; select new
 ; receive watermarks before the ISR is reinstalled. Never discard RX bytes.
 cmp word [uart_software_flow],0
 jne .software
 mov word [uart_tx_paused],0
 mov byte [uart_flow_pending],0
 mov byte [uart_xoff_sent],0
 jmp .hardware
.software:
 cmp word [setup_previous_serial+TI_SOFT],0
 jne .watermark
 mov word [uart_tx_paused],0
 mov byte [uart_flow_pending],0x11
.watermark:
 cmp word [uart_rx_count],128
 jbe .low
 mov byte [uart_xoff_sent],1
 mov byte [uart_flow_pending],0x13
 jmp .hardware
.low:
 mov byte [uart_xoff_sent],0
.hardware:
 mov byte [uart_rts_lowered],0
 cmp word [uart_software_flow],0
 jne .done ;Recovered RX owner selects SOFT first when both flags are enabled.
 cmp word [uart_hardware_flow],0
 je .done
 cmp word [uart_rx_count],128
 jbe .done
 mov byte [uart_rts_lowered],1
.done:
 ret

; SI ASCIIZ prompt. Only the foreground PROGRAM owner paints it, before the
; original screen is restored. No asynchronous overlay/notice is introduced.
terminal_setup_return_prompt:
 mov si,setup_apply_failed
 cmp word [terminal_setup_apply_status],0
 jne .done
 mov si,setup_link_busy
 cmp word [terminal_setup_link_status],3
 je .done
 mov si,setup_unchanged
 cmp word [terminal_setup_outcome+6],0
 jne .deferred
 cmp word [terminal_setup_outcome+4],0
 je .done
 mov si,setup_applied
 ret
.deferred:
 mov si,setup_deferred
 cmp word [terminal_setup_outcome+4],0
 je .done
 mov si,setup_mixed
.done:
 ret
SEGMENT _DATA public class=DATA use16
global terminal_setup_binding_status,terminal_setup_apply_status,terminal_setup_outcome
global terminal_setup_link_status,terminal_setup_key_consumed
terminal_setup_link_status: dw 0 ;0 none,1 applied,2 declined,3 busy/failed.
terminal_setup_key_consumed: dw 0
terminal_setup_binding_status: dw 2
terminal_setup_apply_status: dw 0
terminal_setup_outcome: times 4 dw 0
setup_unchanged: db 13,10,'Setup closed. No active changes. Press a key to return.',0
setup_applied: db 13,10,'Settings applied. Press a key to return.',0
setup_deferred: db 13,10,'Link/profile changes saved for next startup. Press a key to return.',0
setup_mixed: db 13,10,'Settings applied; link/profile changes need restart. Press a key to return.',0
setup_apply_failed: db 13,10,'Could not validate saved settings. Active settings unchanged. Press a key.',0
setup_serial_question: db 13,10,'Apply current-port baud/line/flow now? Peer must match. Y applies; other keys keep link.',0
setup_link_busy: db 13,10,'Line busy; kept current serial settings. Press a key to return.',0
SEGMENT _BSS public align=2 class=BSS use16
global terminal_setup_plan
terminal_setup_plan: resb 624
setup_previous_modem: resb MI_SIZE
setup_previous_serial: resb TI_SIZE
