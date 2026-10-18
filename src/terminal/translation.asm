; Maintained explicit startup XLT import. Native continuation/TX stay raw.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_option_mask,terminal_translation_path,_xlt_dos_read
extern terminal_receive_character,terminal_parser_active
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
 test word [terminal_option_mask],16384
 jz .ok
 cld
 mov ax,terminal_translation_io
 push ax
 mov ax,terminal_translation_table
 push ax
 mov ax,terminal_translation_path
 push ax
 call _xlt_dos_read
 add sp,6
 mov [terminal_translation_status],ax
 or ax,ax
 jnz .bad
 mov word [terminal_translation_enabled],1
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
global terminal_translation_status,terminal_translation_io
terminal_translation_enabled: dw 0
terminal_translation_status: dw 0
terminal_translation_io: times 8 db 0
terminal_translation_table: times 256 db 0
