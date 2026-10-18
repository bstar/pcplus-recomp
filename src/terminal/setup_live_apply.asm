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
extern terminal_config_path,terminal_option_mask,terminal_directory_context
extern terminal_directory_context_valid,terminal_configuration_values
extern terminal_modem_settings,terminal_directory_plan,terminal_dial_target
extern terminal_port_number,terminal_baud_low,terminal_baud_high
extern terminal_parity,terminal_data_bits,terminal_stop_bits,terminal_break_delay_units
extern uart_software_flow,uart_hardware_flow,uart_port_rbr,uart_irq_indices
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
 mov ax,terminal_setup_outcome
 push ax
 mov ax,terminal_setup_plan
 push ax
 call _live_setup_finish
 add sp,4
 mov [terminal_setup_apply_status],ax
 or ax,ax
 jnz .done
 test word [terminal_setup_outcome+4],128
 jz .apply
 ; Prepare future dial/hangup commands only after native expansion validation.
 ; An unexpected prepare failure restores the old settings/commands before
 ; reporting failure. No bytes are sent and connection state is unchanged.
 mov si,terminal_modem_settings
 mov di,setup_previous_modem
 mov cx,MI_SIZE/2
 rep movsw
 mov si,terminal_setup_plan+TI_SIZE
 mov di,terminal_modem_settings
 mov cx,MI_SIZE/2
 rep movsw
 call terminal_connection_prepare
 jnc .apply
 push ds
 pop es
 mov si,setup_previous_modem
 mov di,terminal_modem_settings
 mov cx,MI_SIZE/2
 cld
 rep movsw
 call terminal_connection_prepare
 jnc .failed
 mov word [terminal_exit_code],7
 mov word [terminal_quit],1 ;Cannot continue with unprepared active commands.
.failed:
 mov word [terminal_setup_apply_status],6
 mov word [terminal_setup_outcome],6
 mov word [terminal_setup_outcome+4],0
 jmp .done
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
.done:
 restore

; SI ASCIIZ prompt. Only the foreground PROGRAM owner paints it, before the
; original screen is restored. No asynchronous overlay/notice is introduced.
terminal_setup_return_prompt:
 mov si,setup_apply_failed
 cmp word [terminal_setup_apply_status],0
 jne .done
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
terminal_setup_binding_status: dw 2
terminal_setup_apply_status: dw 0
terminal_setup_outcome: times 4 dw 0
setup_unchanged: db 13,10,'Setup closed. No active changes. Press a key to return.',0
setup_applied: db 13,10,'Settings applied. Press a key to return.',0
setup_deferred: db 13,10,'Link/profile changes saved for next startup. Press a key to return.',0
setup_mixed: db 13,10,'Settings applied; link/profile changes need restart. Press a key to return.',0
setup_apply_failed: db 13,10,'Could not validate saved settings. Active settings unchanged. Press a key.',0
SEGMENT _BSS public align=2 class=BSS use16
global terminal_setup_plan
terminal_setup_plan: resb 624
setup_previous_modem: resb MI_SIZE
