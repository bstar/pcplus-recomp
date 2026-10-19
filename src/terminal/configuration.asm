; Maintained startup-only partial PRM import. Full validation precedes UART IO.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS
%include "terminal_import.inc"
%include "modem_import.inc"
%include "directory_live.inc"
SEGMENT _TEXT public class=CODE use16
extern _terminal_import_read,terminal_config_path,terminal_option_mask
extern _terminal_startup_read,terminal_connection_prepare
extern _terminal_preferences_read,_terminal_directory_preferences_read
extern _terminal_transfer_preferences
extern _directory_live_read_context,terminal_directory_choose
extern terminal_directory_path,terminal_directory_entry,terminal_directory_codes
extern terminal_dial_target
extern terminal_port_number,terminal_baud_low,terminal_baud_high
extern terminal_parity,terminal_data_bits,terminal_stop_bits,terminal_irq_vector
extern uart_port_index,uart_irq_indices,uart_port_rbr,uart_port_thr,uart_port_ier
extern uart_port_lcr,uart_port_mcr,uart_port_lsr,uart_port_msr
extern uart_software_flow,uart_hardware_flow
extern csi_terminal_id,attributes_monochrome,attributes_current
extern attributes_normal_value,attributes_bold_value,attributes_preset_value
extern attributes_reverse_value,attributes_underline_value,render_autowrap,scroll_enabled
extern csi_erase_attribute,cursor_state_saved_1f70
extern attributes_color_mode,terminal_dec_keys,terminal_backspace_mode_9058
extern attributes_bold_active,attributes_blink_active,attributes_reverse_active
extern terminal_macro_pause_character,terminal_macro_character_delay_units

global terminal_load_configuration,terminal_apply_configuration,terminal_apply_display_configuration
global terminal_select_directory
; AX0 continue / AX1 user cancelled / AX8 invalid selectors or browser error.
; No UART access. The optional browser owns and restores its text window.
terminal_select_directory:
 test word [terminal_option_mask],64
 jnz .directory
 test word [terminal_option_mask],384
 jnz .invalid
 xor ax,ax
 ret
.directory:
 test word [terminal_option_mask],16
 jz .invalid
 test word [terminal_option_mask],32
 jnz .invalid
 cmp word [terminal_directory_entry],0
 jne .selected
 call terminal_directory_choose
 cmp ax,2
 jae .invalid
 ret
.selected:
 xor ax,ax
 ret
.invalid:
 mov ax,8
 ret

terminal_load_configuration:
 push bp
 push si
 push di
 push es
 mov word [terminal_configuration_status],0
 mov word [terminal_directory_context_valid],0
 test word [terminal_option_mask],16
 jnz .read
 test word [terminal_option_mask],32
 jz .success
 mov ax,7
 jmp .failure
.read:
 ; The supported C DOS/string subset expects near pointers and DS=SS, DF=0.
 push ds
 pop es
 cld
 test word [terminal_option_mask],64
 jnz .directory
 mov ax,terminal_configuration_io
 push ax
 mov ax,_terminal_transfer_preferences
 push ax
 test word [terminal_option_mask],32
 jz .serial_only
 mov ax,terminal_modem_settings
 push ax
 mov ax,terminal_configuration_values
 push ax
 mov ax,terminal_config_path
 push ax
 call _terminal_preferences_read
 add sp,10
 jmp .loaded
.directory:
 mov ax,_terminal_transfer_preferences
 push ax
 mov ax,terminal_directory_context
 push ax
 mov ax,terminal_directory_io
 push ax
 mov ax,terminal_directory_plan
 push ax
 mov ax,terminal_modem_settings
 push ax
 mov ax,terminal_configuration_values
 push ax
 push word [terminal_directory_codes]
 push word [terminal_directory_entry]
 mov ax,terminal_directory_path
 push ax
 mov ax,terminal_config_path
 push ax
 call _terminal_directory_preferences_read
 add sp,20
 mov [terminal_directory_status],ax
 or ax,ax
 jz .directory_loaded
 mov ax,8
 jmp .loaded
.directory_loaded:
 mov word [terminal_directory_context_valid],1
 push ds
 pop es
 cld
 mov ax,[terminal_directory_plan+DL_MODE]
 mov [terminal_directory_mode],ax
 mov ax,[terminal_directory_plan+DL_PROTOCOL]
 mov [terminal_directory_protocol],ax
 mov si,terminal_directory_plan+DL_TARGET
 mov di,terminal_dial_target
 mov cx,32
 rep movsw
 xor ax,ax
 jmp .loaded
.serial_only:
 xor ax,ax
 push ax ;No modem plan for serial-only startup.
 mov ax,terminal_configuration_values
 push ax
 mov ax,terminal_config_path
 push ax
 call _terminal_preferences_read
 add sp,10
.loaded:
.failure:
 mov [terminal_configuration_status],ax
 or ax,ax
 jnz .done
 call terminal_apply_configuration
 call terminal_connection_prepare
 jnc .success
 mov ax,7
 mov [terminal_configuration_status],ax
 mov word [terminal_directory_context_valid],0
 jmp .done
.success:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Validated structure only, startup before UART ownership. AX/BX/CX/DX scratch.
; CLI category selection wins even when it explicitly selects a default value.
extern _clipboard_separator
extern terminal_break_delay_units
terminal_apply_configuration:
 mov ax,[terminal_configuration_values+TI_CLIPBOARD]
 mov [_clipboard_separator],ax
 test word [terminal_option_mask],96
 jz .serial_settings
 mov ax,[terminal_modem_settings+MI_BREAK_DELAY]
 mov [terminal_break_delay_units],ax
.serial_settings:
 test word [terminal_option_mask],1
 jnz .baud
 mov ax,[terminal_configuration_values+TI_PORT]
 mov [terminal_port_number],ax
 mov ax,[terminal_configuration_values+TI_IRQ]
 mov [uart_irq_indices],ax
 add ax,8
 mov [terminal_irq_vector],ax
 mov word [uart_port_index],0
 mov dx,[terminal_configuration_values+TI_IO_BASE]
 mov [uart_port_rbr],dx
 mov [uart_port_thr],dx
 inc dx
 mov [uart_port_ier],dx
 add dx,2
 mov [uart_port_lcr],dx
 inc dx
 mov [uart_port_mcr],dx
 inc dx
 mov [uart_port_lsr],dx
 inc dx
 mov [uart_port_msr],dx
.baud:
 test word [terminal_option_mask],2
 jnz .line
 mov ax,[terminal_configuration_values+TI_BAUD_LOW]
 mov [terminal_baud_low],ax
 mov ax,[terminal_configuration_values+TI_BAUD_HIGH]
 mov [terminal_baud_high],ax
.line:
 test word [terminal_option_mask],4
 jnz .flow
 mov ax,[terminal_configuration_values+TI_PARITY]
 mov [terminal_parity],ax
 mov ax,[terminal_configuration_values+TI_DATA]
 mov [terminal_data_bits],ax
 mov ax,[terminal_configuration_values+TI_STOP]
 mov [terminal_stop_bits],ax
.flow:
 test word [terminal_option_mask],8
 jnz .display
 mov ax,[terminal_configuration_values+TI_SOFT]
 mov [uart_software_flow],ax
 mov ax,[terminal_configuration_values+TI_HARD]
 mov [uart_hardware_flow],ax
.display:
terminal_apply_display_configuration:
 mov word [attributes_color_mode],1
 mov word [terminal_dec_keys],1
 mov word [terminal_backspace_mode_9058],1
 mov word [attributes_bold_active],0
 mov word [attributes_blink_active],0
 mov byte [attributes_reverse_active],0
 mov ax,[terminal_configuration_values+TI_PROFILE]
 mov [csi_terminal_id],ax
 xor dx,dx
 cmp ax,6
 jne .profile_flag
 inc dx
.profile_flag:
 mov [attributes_monochrome],dx
 mov ax,[terminal_configuration_values+TI_NORMAL]
 mov [attributes_normal_value],ax
 mov [attributes_current],ax
 mov [cursor_state_saved_1f70],ax
 mov [csi_erase_attribute],al
 mov ax,[terminal_configuration_values+TI_BOLD]
 mov [attributes_bold_value],ax
 mov ax,[terminal_configuration_values+TI_PRESET]
 mov [attributes_preset_value],ax
 mov ax,[terminal_configuration_values+TI_REVERSE]
 mov [attributes_reverse_value],ax
 mov ax,[terminal_configuration_values+TI_UNDERLINE]
 mov [attributes_underline_value],ax
 mov ax,[terminal_configuration_values+TI_WRAP]
 mov [render_autowrap],ax
 mov ax,[terminal_configuration_values+TI_SCROLL]
 mov [scroll_enabled],ax
 mov ax,[terminal_configuration_values+TI_MAPPING_PAUSE]
 mov [terminal_macro_pause_character],al
 mov ax,[terminal_configuration_values+TI_MAPPING_DELAY]
 mov [terminal_macro_character_delay_units],ax
 ret

SEGMENT _DATA public class=DATA use16
global terminal_configuration_status,terminal_configuration_io,terminal_configuration_values
global terminal_modem_settings
global terminal_directory_plan,terminal_directory_io,terminal_directory_status
global terminal_directory_mode,terminal_directory_protocol
terminal_configuration_status: dw 0
terminal_configuration_io: times 8 db 0
terminal_configuration_values: times TI_SIZE db 0
terminal_modem_settings: times MI_SIZE db 0
terminal_directory_plan: times DL_SIZE db 0
terminal_directory_io: times DL_RESULT_SIZE db 0
terminal_directory_status: dw 0
terminal_directory_mode: dw 0
terminal_directory_protocol: dw 0

; Opaque context is valid only after successful current directory decoding.
; Not modified by deferred accounting's separate record baseline.
global terminal_directory_context_valid
terminal_directory_context_valid: dw 0
SEGMENT _BSS public align=2 class=BSS use16
global terminal_directory_context
terminal_directory_context: resb DLC_SIZE
