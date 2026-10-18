; Maintained explicit startup XLT import. Native continuation/TX stay raw.
BITS 16
CPU 8086
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_option_mask,terminal_translation_path,_xlt_dos_read
extern _xlt_dos_read_default,process_psp
extern terminal_receive_character,terminal_parser_active
extern terminal_configuration_values,uart_rx_mask
global terminal_load_translation,terminal_translate_input
global terminal_receive_input
; Normal main-loop receive owner; raw monitor/controller/transfers filter first.
terminal_receive_input:
 call terminal_translate_input
 push ax
 inc word [terminal_parser_active]
 call terminal_receive_character
 dec word [terminal_parser_active]
 add sp,2
 ret
terminal_load_translation:
 push bp
 push si
 push di
 push es
 mov word [terminal_translation_enabled],0
 mov word [terminal_translation_mode],0
 mov word [uart_rx_mask],255
 mov word [terminal_translation_status],0
 mov dx,terminal_translation_path
 test word [terminal_option_mask],16384
 jnz .load
 test word [terminal_option_mask],16
 jz .ok
 mov ax,[terminal_configuration_values+TI_TRANSLATION]
 or ax,ax
 jz .ok
 cmp ax,2
 je .seven
 cmp ax,1
 jne .bad
 mov ax,terminal_translation_io
 push ax
 mov ax,terminal_translation_table
 push ax
 push word [process_psp]
 call _xlt_dos_read_default
 jmp .loaded
.load:
 cld
 mov ax,terminal_translation_io
 push ax
 mov ax,terminal_translation_table
 push ax
 push dx
 call _xlt_dos_read
.loaded:
 add sp,6
 mov [terminal_translation_status],ax
 or ax,ax
 jnz .bad
 mov word [terminal_translation_enabled],1
 mov word [terminal_translation_mode],1
 jmp .ok
.seven:
 mov word [uart_rx_mask],127
 mov word [terminal_translation_mode],2
.ok:
 xor ax,ax
 jmp .done
.bad:
 mov ax,12
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; AX contains an actual dequeued byte. No table mutation or UART-ring write.
; Keep disabled behavior byte-identical and preserve caller BX.
terminal_translate_input:
 cmp word [terminal_translation_enabled],0
 je .done
 push bx
 mov bx,ax
 and bx,255
 mov al,[terminal_translation_table+bx]
 xor ah,ah
 pop bx
.done:
 ret
SEGMENT _DATA public class=DATA use16
global terminal_translation_enabled,terminal_translation_table
global terminal_translation_mode
global terminal_translation_status,terminal_translation_io
terminal_translation_enabled: dw 0
terminal_translation_mode: dw 0
terminal_translation_status: dw 0
terminal_translation_io: times 8 db 0
terminal_translation_table: times 256 db 0
