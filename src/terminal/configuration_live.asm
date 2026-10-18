; Apply validated configured display/mapping values without resetting the
; parser, screen, cursor, peer SGR/DEC modes, keymap or transport. AX TI42.
BITS 16
CPU 8086
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_configuration_values,terminal_reset_patch_word,terminal_reset_patch_byte
extern attributes_normal_value,attributes_bold_value,attributes_preset_value
extern attributes_reverse_value,attributes_underline_value,attributes_current
extern attributes_bold_active,attributes_blink_active,attributes_reverse_active
extern cursor_state_saved_1f70,csi_erase_attribute,csi_wrap_pending
extern render_autowrap,scroll_enabled
extern terminal_macro_pause_character,terminal_macro_character_delay_units
global terminal_apply_live_configuration
terminal_apply_live_configuration:
 push bp
 push si
 push di
 push es
 mov bp,ax
 mov si,live_display_fields
 mov cx,7
 cld
.field:
 lodsw
 mov di,ax
 lodsw
 mov bx,ax
 mov dx,[bp+di]
 cmp dx,[terminal_configuration_values+di]
 je .next
 mov [bx],dx
 call terminal_reset_patch_word
 cmp di,TI_WRAP
 jne .normal
 mov word [csi_wrap_pending],0
.normal:
 cmp di,TI_NORMAL
 jne .next
 ; Preserve the peer's active SGR. A currently plain old normal attribute can
 ; adopt the new normal; other live attributes wait for their next SGR change.
 mov ax,[terminal_configuration_values+TI_NORMAL]
 cmp ax,[attributes_current]
 jne .baseline
 cmp word [attributes_bold_active],0
 jne .baseline
 cmp word [attributes_blink_active],0
 jne .baseline
 cmp byte [attributes_reverse_active],0
 jne .baseline
 mov [attributes_current],dx
 mov [csi_erase_attribute],dl
.baseline:
 mov ax,attributes_current
 call terminal_reset_patch_word
 mov ax,cursor_state_saved_1f70
 call terminal_reset_patch_word
 mov ax,csi_erase_attribute
 call terminal_reset_patch_byte
.next:
 loop .field
 mov ax,[bp+TI_MAPPING_PAUSE]
 mov [terminal_macro_pause_character],al
 mov ax,[bp+TI_MAPPING_DELAY]
 mov [terminal_macro_character_delay_units],ax
 mov si,bp
 mov di,terminal_configuration_values
 push ds
 pop es
 mov cx,TI_SIZE/2
 rep movsw
 xor ax,ax
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
live_display_fields:
 dw TI_NORMAL,attributes_normal_value
 dw TI_BOLD,attributes_bold_value
 dw TI_PRESET,attributes_preset_value
 dw TI_REVERSE,attributes_reverse_value
 dw TI_UNDERLINE,attributes_underline_value
 dw TI_WRAP,render_autowrap
 dw TI_SCROLL,scroll_enabled
