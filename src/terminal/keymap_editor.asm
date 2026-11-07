; Native Alt-F8 helper through the existing drained PROGRAM/display owner.
BITS 16
CPU 8086
%ifdef TERMINAL_KEYMAP_EDITOR
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_kind,terminal_keymap_marker
global terminal_keymap_queue
terminal_keymap_queue:
 mov ax,terminal_keymap_marker
 global terminal_keymap_queue_common_site
 terminal_keymap_queue_common_site equ $
 call terminal_program_start
 or ax,ax
 jnz .done
 mov word [terminal_program_kind],13
.done:
 retf

extern terminal_read_foreground_key
global terminal_keymap_read_key
terminal_keymap_read_key:
 call terminal_read_foreground_key
 retf

SEGMENT KEYMAP_CODE public align=16 class=FARCODE use16
GROUP KEYMAP_GROUP KEYMAP_CODE
extern _keymap_live_prepare_far,_keymap_live_reload_far
extern keyboard_bios_mode
extern terminal_program_result,terminal_exit_code,terminal_quit,terminal_program_status
extern terminal_translation_edit_executable,terminal_translation_edit_tail
extern terminal_keymap_read_key
extern process_psp
extern terminal_recording_owned_far
extern terminal_parser_active,terminal_macro_active,terminal_transfer_pending,terminal_transfer_active
extern terminal_monitor_active,terminal_controller_active,terminal_snapshot_active
extern terminal_ansi_wait_active,_redisplay_active
global terminal_keymap_edit_start,terminal_keymap_edit_prepare,terminal_keymap_edit_complete
safe:
 call far terminal_recording_owned_far
 or ax,ax
 jnz .done
 mov ax,[terminal_parser_active]
 or ax,[terminal_macro_active]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_snapshot_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[_redisplay_active]
.done: ret
terminal_keymap_edit_start:
 call safe
 or ax,ax
 jnz .done
 global terminal_keymap_queue_site
 terminal_keymap_queue_site equ $
 call far terminal_keymap_queue
.done: retf
terminal_keymap_edit_prepare:
 cld
 call safe
 or ax,ax
 jnz .done
 mov ax,terminal_translation_edit_tail
 push ax
 mov ax,terminal_translation_edit_executable
 push ax
 push word [process_psp]
 global terminal_keymap_cprepare_site
 terminal_keymap_cprepare_site equ $
 call far _keymap_live_prepare_far
 add sp,6
 or ax,ax
 jnz .done
 cmp byte [keyboard_bios_mode],0
 jne .done
 mov di,terminal_translation_edit_tail
 mov cx,87
.find:
 cmp byte [di],0
 je .append
 inc di
 loop .find
 mov ax,1
 jmp .done
.append:
 mov si,legacy
.copy:
 cs lodsb
 mov [di],al
 inc di
 or al,al
 jnz .copy
.done: retf
terminal_keymap_edit_complete:
 ; Recovery exit14 is quarantined; never adopt potentially disputed file bytes.
 cmp word [terminal_program_result],0
 jne .reload
 cmp byte [terminal_program_result+5],0
 jne .fatal
.reload:
 cmp word [terminal_program_result+4],14
 je .fatal
 global terminal_keymap_creload_site
 terminal_keymap_creload_site equ $
 call far _keymap_live_reload_far
 cmp ax,14
 je .fatal
 or ax,ax
 jnz .message
 cmp word [terminal_program_status],4
 je .done
.message:
 mov si,failed
 call text
 ; The existing foreground reader is near. Its far keyboard adapter is shared.
 call far terminal_keymap_read_key
.done: retf
.fatal:
 mov word [terminal_exit_code],14
 mov word [terminal_quit],1
 retf
text:
 cs lodsb
 or al,al
 jz .done
 mov ah,0x0e
 xor bh,bh
 mov bl,7
 int 0x10
 jmp text
.done: ret
legacy: db ' /LEGACY',0
failed: db 13,10,'Keyboard configuration error. Press a key.',0
%endif
