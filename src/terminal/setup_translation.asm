; Confirmed input-mode handoff inside the already-quiesced settings owner.
BITS 16
CPU 8086
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern _xlt_live_bind,_xlt_live_stage,_xlt_live_commit,process_psp
extern terminal_option_mask,terminal_setup_plan,terminal_setup_outcome
extern terminal_setup_key_consumed,terminal_parser_active
extern terminal_transfer_pending,terminal_transfer_active
extern terminal_monitor_active,terminal_controller_active
extern terminal_translation_mode,terminal_translation_enabled,terminal_translation_table
extern uart_rx_mask
global terminal_setup_translation_bind,terminal_setup_translation_choice
global terminal_setup_translation_commit
terminal_setup_translation_bind:
 mov word [terminal_setup_translation_status],0
 mov word [terminal_setup_translation_io],0
 mov word [terminal_setup_translation_io+2],0
 mov word [terminal_setup_translation_io+4],0
 mov word [terminal_setup_translation_io+6],0
 test word [terminal_option_mask],16384
 jnz .done
 push word [process_psp]
 call _xlt_live_bind
 add sp,2
.done:
 ret

translation_safe:
 mov ax,[terminal_parser_active]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 ret

terminal_setup_translation_choice:
 test word [terminal_setup_outcome+4],2048
 jz .done
 call translation_safe
 jnz translation_busy
 mov ax,terminal_setup_translation_io
 push ax
 push word [terminal_setup_plan+TI_TRANSLATION]
 call _xlt_live_stage
 add sp,4
 or ax,ax
 jnz translation_failed
 mov si,translation_question
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
 mov word [terminal_setup_translation_status],2
 jmp translation_defer
.accept:
 mov word [terminal_setup_translation_status],1
.done:
 ret

terminal_setup_translation_commit:
 test word [terminal_setup_outcome+4],2048
 jz .done
 call translation_safe
 jnz translation_busy
 mov ax,terminal_translation_table
 push ax
 push word [terminal_setup_plan+TI_TRANSLATION]
 call _xlt_live_commit
 add sp,4
 mov [terminal_setup_translation_io],ax
 or ax,ax
 jnz translation_failed
 mov ax,[terminal_setup_plan+TI_TRANSLATION]
 mov [terminal_translation_mode],ax
 mov word [terminal_translation_enabled],0
 mov word [uart_rx_mask],255
 cmp ax,1
 jne .mask
 mov word [terminal_translation_enabled],1
.mask:
 cmp ax,2
 jne .done
 mov word [uart_rx_mask],127
.done:
 ret
translation_busy:
 mov word [terminal_setup_translation_io],7
translation_failed:
 mov word [terminal_setup_translation_status],3
translation_defer:
 and word [terminal_setup_outcome+4],~2048
 or word [terminal_setup_outcome+6],2048
 mov ax,[terminal_translation_mode]
 mov [terminal_setup_plan+TI_TRANSLATION],ax
 ret

SEGMENT _DATA public class=DATA use16
global terminal_setup_translation_status,terminal_setup_translation_io
terminal_setup_translation_status: dw 0 ;0none,1accepted,2declined,3load/ownership failure.
terminal_setup_translation_io: times 4 dw 0
translation_question: db 13,10,'Apply input translation now? Queued input uses the new mode. Y applies; other keys keep mode.',0
