; Direct source-built XLTEDIT child over the existing drained foreground owner.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_translation_reload_safe,terminal_translation_reload_run
extern terminal_translation_reload_status,terminal_program_status
extern terminal_program_start,terminal_program_kind,process_psp
extern _xlt_live_editor,terminal_read_foreground_key,terminal_connection_notice
global terminal_translation_edit_start,terminal_translation_edit_prepare
global terminal_translation_edit_complete

terminal_translation_edit_start:
 push si
 call terminal_translation_reload_safe
 or ax,ax
 jnz .denied
 mov ax,edit_command
 call terminal_program_start
 or ax,ax
 jnz .denied
 mov word [terminal_program_kind],3
 mov word [terminal_translation_edit_status],1
 pop si
 ret
.denied:
 mov word [terminal_translation_edit_status],4
 mov si,edit_unavailable
 call terminal_connection_notice
 mov ax,1
 pop si
 ret

; Called only after UART/IRQ handoff. Pure argument construction precedes EXEC.
terminal_translation_edit_prepare:
 call terminal_translation_reload_safe
 or ax,ax
 jnz .unsafe
 mov ax,terminal_translation_edit_tail
 push ax
 mov ax,terminal_translation_edit_executable
 push ax
 push word [process_psp]
 call _xlt_live_editor
 add sp,6
 or ax,ax
 jz .done
 mov word [terminal_translation_edit_status],7
 ret
.unsafe:
 mov word [terminal_translation_edit_status],6
 mov ax,1
.done:
 ret

; PROGRAM has quieted the child's UART before any prompt or disk reload here.
terminal_translation_edit_complete:
 push si
 cmp word [terminal_program_status],4
 jne .failed
 call terminal_translation_reload_run
 mov ax,[terminal_translation_reload_status]
 mov [terminal_translation_edit_status],ax
 pop si
 ret
.failed:
 cmp word [terminal_translation_edit_status],6
 je .message
 mov word [terminal_translation_edit_status],7
.message:
 mov si,edit_failed
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
 call terminal_read_foreground_key
 pop si
 ret

SEGMENT _DATA public class=DATA use16
global terminal_translation_edit_executable,terminal_translation_edit_tail
global terminal_translation_edit_status
terminal_translation_edit_executable: times 64 db 0
terminal_translation_edit_tail: times 96 db 0
terminal_translation_edit_status: dw 0 ;1queued,2applied,3declined,4unavailable,5read,6unsafe,7child.
edit_command: db 'XLTEDIT',0
edit_unavailable: db 'Input table editor unavailable.',0
edit_failed: db 13,10,'Input table editor failed; active table retained. Press a key.',0
