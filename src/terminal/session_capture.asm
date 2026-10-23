; Internal foreground snapshot: AX near628-byte plan, DX optional near66-byte
; transfer plan, BX policy0 legacy setup /1 actual session. Return AX0/1 invalid
; destination/policy,2 CPU context. Preserve BX/CX/DX/SI/DI/BP/ES and DS/SS.
; Destinations are the existing setup plan or caller-owned live stack objects;
; no allocation, IO, hardware access or active settings mutation.
BITS 16
CPU 8086
%ifdef TERMINAL_SESSION_CAPTURE
%include "terminal_import.inc"
%include "modem_import.inc"
%include "directory_live.inc"
%define PLAN_SIZE (TI_SIZE+MI_SIZE+DL_SIZE+2)
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
extern terminal_configuration_values,terminal_modem_settings,terminal_directory_plan
extern _terminal_transfer_preferences,terminal_setup_plan,terminal_stack_top
extern terminal_port_number,terminal_baud_low,terminal_baud_high
extern terminal_parity,terminal_data_bits,terminal_stop_bits,terminal_break_delay_units
extern uart_software_flow,uart_hardware_flow,uart_port_rbr,uart_irq_indices
extern terminal_translation_mode,_clipboard_separator,csi_terminal_id
extern attributes_normal_value,attributes_bold_value,attributes_preset_value
extern attributes_reverse_value,attributes_underline_value,render_autowrap,scroll_enabled
extern terminal_macro_pause_character,terminal_macro_character_delay_units
extern terminal_modem_pause
global terminal_session_capture_far
terminal_session_capture_far:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov di,ax
 mov ax,ds
 mov cx,ss
 cmp ax,cx
 jne .context
 mov cx,seg terminal_setup_plan
 cmp ax,cx
 jne .context
 pushf
 pop ax
 test ax,0x400
 jnz .context
 test ax,0x200
 jz .context
 cmp bx,1
 ja .invalid
 cmp di,terminal_setup_plan
 je .plan_ok
 mov ax,di
 mov cx,PLAN_SIZE
 call .stack_extent
 jc .invalid
.plan_ok:
 or dx,dx
 jz .outputs_ok
 mov ax,dx
 mov cx,66
 call .stack_extent
 jc .invalid
 ; Pairwise separation, using nonwrapping checked extents.
 mov ax,di
 add ax,PLAN_SIZE
 cmp ax,dx
 jbe .outputs_ok
 mov ax,dx
 add ax,66
 cmp ax,di
 ja .invalid
.outputs_ok:
 push ds
 pop es
 push di
 mov si,terminal_configuration_values
 mov cx,TI_SIZE/2
 rep movsw
 mov si,terminal_modem_settings
 mov cx,MI_SIZE/2
 rep movsw
 mov si,terminal_directory_plan
 mov cx,DL_SIZE/2
 rep movsw
 xor ax,ax
 stosw
 pop di
 %macro actual 2
 mov ax,[%2]
 mov [di+%1],ax
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
 actual TI_TRANSLATION,terminal_translation_mode
 actual TI_CLIPBOARD,_clipboard_separator
 actual TI_SIZE+MI_BREAK_DELAY,terminal_break_delay_units
 or bx,bx
 jz .transfer
 actual TI_PROFILE,csi_terminal_id
 actual TI_NORMAL,attributes_normal_value
 actual TI_BOLD,attributes_bold_value
 actual TI_PRESET,attributes_preset_value
 actual TI_REVERSE,attributes_reverse_value
 actual TI_UNDERLINE,attributes_underline_value
 actual TI_WRAP,render_autowrap
 actual TI_SCROLL,scroll_enabled
 xor ax,ax
 mov al,[terminal_macro_pause_character]
 mov [di+TI_MAPPING_PAUSE],ax
 mov al,[terminal_modem_pause]
 mov [di+TI_SIZE+MI_PAUSE_CHARACTER],ax
 actual TI_MAPPING_DELAY,terminal_macro_character_delay_units
.transfer:
 or dx,dx
 jz .success
 mov di,dx
 mov si,_terminal_transfer_preferences
 mov cx,33
 rep movsw
.success:
 xor ax,ax
 jmp .done
.context:
 mov ax,2
 jmp .done
.invalid:
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
; AX/CX destination/size. Entire object must lie in live caller stack storage,
; above our incoming far return frame. Caller owns allocation/lifetime there.
.stack_extent:
 cmp ax,terminal_stack_top-8192
 jb .bad_extent
 push si
 lea si,[bp+6]
 cmp ax,si
 pop si
 jb .bad_extent
 add ax,cx
 jc .bad_extent
 cmp ax,terminal_stack_top
 ja .bad_extent
 clc
 ret
.bad_extent:
 stc
 ret
%endif
