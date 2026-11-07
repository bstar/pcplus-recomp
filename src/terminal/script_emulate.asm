; Optional parent-owned script profile transaction. Maintained safety policy:
; preflight/stage keyboard before full reset;4/6 only. No RPC exposure yet.
BITS 16
CPU 8086
%ifdef ASPECT_EMULATE_POLICY
%include "terminal_import.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_setup_profile_stage,terminal_setup_profile_finish
script_emulate_stage_resident:
 call terminal_setup_profile_stage
 retf
script_emulate_finish_resident:
 call terminal_setup_profile_finish
 retf
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern _aspect_render_admit
extern terminal_setup_profile_ready,terminal_setup_profile_status
extern terminal_configuration_values,terminal_quit,setup_profile_keyboard_io
extern terminal_script_window_active,terminal_script_confirm_active
extern terminal_editor_screen_owned,terminal_browser_screen_owned
extern _command_menu_active,_redisplay_active
; AX target, AX typed ASPECT result; all other registers and FLAGS preserved.
; Requires the parent's live script admission. Never acquires/changes UART.
global terminal_script_emulate
terminal_script_emulate:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cld
 mov si,ax
 or ah,ah
 jnz .operand
 cmp ax,4
 je .supported
 cmp ax,6
 jne .unsupported
.supported:
 ; Every nonzero owner has the same typed state outcome. Fold the checks
 ; without changing their admission semantics or discarding any owner.
 mov ax,[cs:script_emulate_quarantined]
 or ax,[terminal_setup_profile_ready]
 or ax,[cs:terminal_script_window_active]
 or ax,[cs:terminal_script_confirm_active]
 or ax,[_command_menu_active]
 or ax,[_redisplay_active]
 or ax,[terminal_quit]
 jnz .state
 mov al,[terminal_editor_screen_owned]
 or al,[terminal_browser_screen_owned]
 jnz .state
 call _aspect_render_admit
 or ax,ax
 jnz .done
 mov ax,si
 call far script_emulate_stage_resident
 cmp ax,2
 je .unsupported
 or ax,ax
 jnz .io
 ; A synchronous foreground transaction cannot yield to a different owner
 ; between stage and commit. Stage does not poll parser/receive callbacks.
 mov di,[terminal_setup_profile_status]
 mov ax,si
 mov [terminal_configuration_values+TI_PROFILE],ax
 mov word [terminal_setup_profile_status],1
 call far script_emulate_finish_resident
 cmp word [terminal_setup_profile_status],1
 jne .state
 mov [terminal_setup_profile_status],di
 xor ax,ax
 jmp .done
.io:
 cmp word [setup_profile_keyboard_io+4],0
 je .io_result
 mov word [cs:script_emulate_quarantined],1
.io_result:
 mov ax,5
 jmp .done
.unsupported:
 mov ax,3
 jmp .done
.operand:
 mov ax,7
 jmp .done
.state:
 mov ax,10
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf
; Unknown DOS-close outcome cannot be repaired by reopening the path.
; No handle identity escapes the strict reader; retain this owner quarantine
; until process restart rather than guessing a handle to close or retrying.
script_emulate_quarantined: dw 0
%endif
