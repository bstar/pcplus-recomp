; Shared real terminal renderer, retained across a checked ASPECT child lease.
; Application policy lives in ASPECT_CODE; small resident adapters retain the
; native near/cdecl ABIs. No capability is published until script prepare.
BITS 16
CPU 8086
%include "resident_bridge.inc"
%ifdef ASPECT_NOTICE_INPUT
 %define RENDER_CAPABILITY 16
 extern _terminal_sound_enabled,terminal_program_result,_terminal_mouse_selected_scale
%else
%ifdef ASPECT_SOUND_POLICY
 %define RENDER_CAPABILITY 15
 extern _terminal_sound_enabled,terminal_program_result
%elifdef ASPECT_EXTERNAL_RENDER
 %define RENDER_CAPABILITY 13
 extern terminal_program_result
%else
 %define RENDER_CAPABILITY 12
%endif
%endif
SEGMENT _TEXT public class=CODE use16
extern terminal_receive_character,terminal_stack_top,process_psp
extern terminal_program_active,terminal_program_kind
extern terminal_parser_active,terminal_ansi_wait_active
extern terminal_receive_character_native,csi_set_modes,csi_reset_modes
extern _script_render_offset,_script_render_segment,_script_render_token,_script_render_version
global terminal_aspect_emit_resident
global terminal_receive_character,terminal_aspect_set_modes,terminal_aspect_reset_modes
terminal_receive_character:
 cmp word [terminal_aspect_active],0
 je .native
 push bp
 mov bp,sp
 inc word [terminal_parser_active]
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,[bp+4]
 call far terminal_render_control
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 push word [bp+4]
 call terminal_receive_character_native
 add sp,2
 dec word [terminal_parser_active]
 pop bp
 ret
.native:
 jmp terminal_receive_character_native
terminal_aspect_set_modes:
 cmp word [terminal_aspect_active],0
 je .native
 call far terminal_render_set_modes
.native:
 jmp csi_set_modes
terminal_aspect_reset_modes:
 cmp word [terminal_aspect_active],0
 je .native
 call far terminal_render_reset_modes
.native:
 jmp csi_reset_modes
terminal_aspect_emit_resident:
 push ax
 call terminal_receive_character
 add sp,2
 retf

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern resident_bridge_initialize,resident_bridge_disable,resident_bridge_entry
extern resident_bridge_caller_ds,resident_bridge_callback,resident_bridge_abort
extern _aspect_render_admit,_aspect_render_preflight_control
extern _aspect_render_preflight_modes
extern _aspect_render_client_admit
extern terminal_status_live,terminal_break_ui,terminal_script_label_update
extern terminal_break_delay_units
extern keyboard_bios_mode
extern terminal_key_output
extern terminal_script_window_open,terminal_script_window_service
extern terminal_script_window_hide,terminal_script_window_close,terminal_script_confirm,terminal_script_confirm_active
extern terminal_script_window_cooperative
global terminal_script_window_poll
global render_child_ds,render_started,render_body,render_attached,render_child_psp
extern _script_handoff
global terminal_render_prepare,terminal_render_revoke,terminal_render_validate,terminal_render_typed_abort
global terminal_render_failure_notice
global terminal_render_unsupported,terminal_render_read,terminal_render_read_now
global terminal_render_unread,terminal_render_send,terminal_render_string
global terminal_render_poll,terminal_render_cancel
global terminal_render_control,terminal_render_set_modes,terminal_render_reset_modes
terminal_render_prepare:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call resident_bridge_disable
 or ax,ax
 jnz .done
 mov word [terminal_aspect_active],0
 mov word [terminal_aspect_adopt],0
 mov word [terminal_script_label_valid],0
 mov word [cs:render_attached],0
%ifdef ASPECT_EXTERNAL_RENDER
 mov word [cs:render_program_owned],0
%endif
 mov word [cs:render_callback],0
 mov word [cs:render_callback+2],0
 call _aspect_render_admit
 or ax,ax
 jnz .done
 mov bx,terminal_stack_top-8192+16
 mov cx,terminal_stack_top-8192+16+4096
 mov dx,render_body
 mov si,seg render_proxy
 mov di,render_proxy
 call resident_bridge_initialize
 or ax,ax
 jnz .done
 inc word [cs:render_token]
 jnz .token
 inc word [cs:render_token]
.token:
 mov word [_script_render_offset],resident_bridge_entry
 mov word [_script_render_segment],seg resident_bridge_entry
 mov ax,[cs:render_token]
 mov [_script_render_token],ax
 mov word [_script_render_version],RENDER_CAPABILITY
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf

terminal_render_revoke:
 call terminal_script_window_close
 ; Parent cursor cleanup needs no retired child callback or UART operation.
 push bx
 mov bx,1
 call far terminal_break_ui
 pop bx
 call resident_bridge_disable
 mov word [cs:render_attached],0
%ifdef ASPECT_EXTERNAL_RENDER
 mov word [cs:render_program_owned],0
%endif
 mov word [cs:render_callback],0
 mov word [cs:render_callback+2],0
 mov word [terminal_aspect_active],0
 mov word [terminal_script_label_valid],0
 retf

terminal_render_validate:
 mov ax,1
 cmp word [_script_render_offset],resident_bridge_entry
 jne .done
 cmp word [_script_render_segment],seg resident_bridge_entry
 jne .done
 mov ax,[cs:render_token]
 cmp [_script_render_token],ax
 mov ax,1
 jne .done
 cmp word [_script_render_version],RENDER_CAPABILITY
 jne .done
 xor ax,ax
.done:
 retf

; Invoked after parent IRQ reacquisition. No retired child callbacks, BIOS
; teletype or old screen restoration are used for an admitted script failure.
terminal_render_failure_notice:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 cld
 mov si,render_failure_text
.next:
 mov al,[cs:si]
 inc si
 or al,al
 jz .done
 xor ah,ah
 call far terminal_aspect_emit_resident
 jmp .next
.done:
%ifdef ASPECT_EXTERNAL_RENDER
 cmp byte [terminal_program_result+5],3 ;DOS4D retained-process mode.
 jne .notice_finished
 mov si,render_retained_text
.retained:
 mov al,[cs:si]
 inc si
 or al,al
 jz .notice_finished
 xor ah,ah
 call far terminal_aspect_emit_resident
 jmp .retained
.notice_finished:
%endif
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
render_failure_text: db 13,10,'ASPECT returned an error.',13,10,0
%ifdef ASPECT_EXTERNAL_RENDER
render_retained_text: db 'ASPECT memory retained.',13,10,0
%endif

render_psp:
 push bx
 mov ah,0x62
 int 0x21
 mov ax,bx
 pop bx
 ret

render_body:
 mov di,ax
 call resident_bridge_caller_ds
 mov [cs:render_caller_ds],ax
 call render_psp
 mov [cs:render_caller_psp],ax
 cmp word [terminal_program_active],1
 jne .state
 cmp word [terminal_program_kind],4
 jne .state
 cmp di,0
 je .begin
 cmp word [cs:render_attached],1
 jne .state
 cmp ax,[cs:render_child_psp]
 jne .state
 mov ax,[cs:render_caller_ds]
 cmp ax,[cs:render_child_ds]
 jne .state
%ifdef ASPECT_NOTICE_INPUT
 cmp di,14
 je .mouse_policy
%endif
%ifdef ASPECT_SOUND_POLICY
 cmp di,13
 je .sound_policy
%endif
%ifdef ASPECT_EXTERNAL_RENDER
 cmp di,10
 je .program_end
 cmp word [cs:render_program_owned],0
 jne .state
 cmp di,9
 je .program_begin
%endif
 cmp di,12
 je .abort_confirm
 cmp di,11
 je .window_service
 cmp di,2
 je .end
 cmp di,3
 je .status
 cmp di,4
 je .break_policy
 cmp di,5
 je .break_notice
 cmp di,6
 je .script_label
 cmp di,7
 je .keyboard_policy
 cmp di,8
 je .key
 cmp di,1
 jne .state
 cmp bx,255
 ja .operand
 call terminal_script_window_hide
 mov ax,[terminal_parser_active]
 mov [cs:render_saved_parser],ax
 mov ax,[terminal_ansi_wait_active]
 mov [cs:render_saved_wait],ax
 call render_tick
 mov [cs:render_started],ax
 mov word [cs:render_remaining],4096
 mov word [terminal_aspect_active],1
 mov ax,bx
 call far terminal_aspect_emit_resident
 call render_scope_end
 xor ax,ax
.done:
 ret
.status:
 ; returned is published last after child UART restoration. Unlike ordinary
 ; error rendering, STATUS reads hardware carrier and requires that lease.
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 ; This is the captured bridge's checked parent stack. No child pointers,
 ; receive callbacks, FILE activity or parser entry are used by STATUS.
 call terminal_script_window_hide
 call far terminal_status_live
 ret
%ifdef ASPECT_SOUND_POLICY
.sound_policy:
 or bx,bx
 jnz .operand
 cmp word [_script_handoff+22],0
 jne .serial
 ; Scalar, read-only policy is valid during an owned PROGRAM lease.
 ; No receive/parser/callback or temporary window state is entered.
 mov ax,[_terminal_sound_enabled]
 and ax,1
 or ax,0xff00
 ret
%endif
%ifdef ASPECT_NOTICE_INPUT
.mouse_policy:
 cmp bx,1
 ja .operand
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call far _terminal_mouse_selected_scale
 add sp,2
 cmp ax,1
 jb .state
 cmp ax,999
 ja .state
 or ax,0xf000
 ret
%endif
.break_policy:
 or bx,bx
 jnz .operand
 cmp word [_script_handoff+22],0
 jne .serial
 call _aspect_render_admit
 or ax,ax
 jnz .done
 mov bx,[terminal_break_delay_units]
 mov ax,6
 call resident_bridge_callback
 cmp ax,14
 jbe .done
 jmp .state
.break_notice:
 cmp bx,1
 ja .operand
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 call terminal_script_window_hide
 call far terminal_break_ui
 ret
.keyboard_policy:
 or bx,bx
 jnz .operand
 cmp word [_script_handoff+22],0
 jne .serial
 call _aspect_render_admit
 or ax,ax
 jnz .done
 xor bx,bx
 mov bl,[keyboard_bios_mode]
 cmp bx,0
 je .keyboard_mode
 cmp bx,16
 jne .state
.keyboard_mode:
 mov ax,8
 call resident_bridge_callback
 cmp ax,14
 jbe .done
 jmp .state
.key:
 cmp word [cs:terminal_script_confirm_active],0
 jne .state
 cmp word [cs:terminal_script_window_cooperative],0
 jne .state
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 push bx
 xor bx,bx
 mov ax,9
 call resident_bridge_callback
 mov si,ax
 mov ax,4
 call resident_bridge_callback
 or ax,ax
 jnz .key_error
 cmp si,0xffff
 je .key_policy_ok
 cmp si,255
 ja .key_state
.key_policy_ok:
 pop ax
 mov bx,si
 push ax
 mov ax,[terminal_parser_active]
 mov [cs:render_saved_parser],ax
 mov ax,[terminal_ansi_wait_active]
 mov [cs:render_saved_wait],ax
 call render_tick
 mov [cs:render_started],ax
 mov word [cs:render_remaining],4096
 mov word [terminal_aspect_active],1
 pop ax
 cmp ax,0x2c00
 jne .ordinary_key
 call terminal_script_window_open
 or ax,ax
 jnz .key_finished
 call window_publish
 jmp .key_finished
.ordinary_key:
 call terminal_script_window_hide
 call far terminal_key_output
.key_finished:
 push ax
 call render_scope_end
 pop ax
 ret
.key_state:
 mov ax,10
.key_error:
 pop bx
 cmp ax,14
 jbe .done
 mov ax,10
 ret
.script_label:
 cmp bx,0xffff
 je .label_admit
 cmp bx,255
 ja .operand
.label_admit:
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 push bp
 mov bp,sp
 sub sp,16
 mov [bp-2],bx
 push ds
 pop es
 lea di,[bp-16]
 xor ax,ax
 mov cx,13
 rep stosb
 lea di,[bp-16]
 xor cx,cx
.label_pull:
 mov bx,cx
 mov ax,7
 call resident_bridge_callback
 push ax
 xor bx,bx
 mov ax,4
 call resident_bridge_callback
 or ax,ax
 jnz .label_callback_error
 pop ax
 cmp ax,255
 ja .label_state
 or al,al
 jz .label_complete
 cmp cx,12
 jae .label_operand
 cmp al,32
 jb .label_operand
 cmp al,127
 je .label_operand
 cmp al,0x5c
 je .label_operand
 cmp al,':'
 je .label_operand
 cmp al,'/'
 je .label_operand
 mov [di],al
 inc di
 inc cx
 jmp .label_pull
.label_complete:
 mov byte [di],0
 cmp cx,5
 jb .label_operand
 cmp byte [di-4],'.'
 jne .label_operand
 cmp byte [di-3],'A'
 jne .label_operand
 cmp byte [di-2],'S'
 jne .label_operand
 cmp byte [di-1],'X'
 jne .label_operand
 lea si,[bp-16]
 sub cx,4
.label_stem:
 lodsb
 cmp al,'.'
 je .label_operand
 loop .label_stem
 lea si,[bp-16]
 mov bx,[bp-2]
 call terminal_script_window_hide
 call far terminal_script_label_update
 jmp .label_return
.label_callback_error:
 pop dx
 cmp ax,14
 jbe .label_return
.label_state:
 mov ax,10
 jmp .label_return
.label_operand:
 mov ax,7
.label_return:
 mov sp,bp
 pop bp
 ret
.serial:
 mov ax,14
 ret
%ifdef ASPECT_EXTERNAL_RENDER
.program_begin:
 cmp word [cs:terminal_script_confirm_active],0
 jne .state
 cmp bx,1
 ja .operand
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 call terminal_script_window_close
 inc bx ;1 NOCLEAR,2 SAVE; zero means no external owner.
 mov [cs:render_program_owned],bx
 inc word [cs:render_program_begins]
 xor ax,ax
 ret
.program_end:
 cmp word [cs:render_program_owned],0
 je .state
 cmp bx,1
 ja .operand
 ; A saved view cannot request the native NOCLEAR geometry refresh.
 cmp bx,0
 je .program_retire
 cmp word [cs:render_program_owned],1
 jne .state
 inc word [cs:render_program_refreshes]
.program_retire:
 mov word [cs:render_program_owned],0
 inc word [cs:render_program_ends]
 cmp word [_script_handoff+22],0
 jne .serial
 ; PROGRAM has restored BIOS geometry and the saved cursor. Parent metadata
 ; never left this suspended allocation. Re-admit the actual fixed80x25 view,
 ; including NOCLEAR/raw247 refresh; do not RIS-clear the child's visible text
 ; or replace the profile/keymap/history with startup defaults.
 call _aspect_render_admit
 ret
%endif
.begin:
 cmp word [cs:render_attached],0
 jne .state
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 sub sp,4
 mov di,sp
 push di
 push word [cs:render_token]
 push bx
 push word [cs:render_caller_ds]
 push word [process_psp]
 push word [cs:render_caller_psp]
 call _aspect_render_client_admit
 add sp,12
 or ax,ax
 jnz .client_bad
 pop ax
 mov [cs:render_callback],ax
 pop ax
 mov [cs:render_callback+2],ax
 mov ax,[cs:render_caller_ds]
 mov [cs:render_child_ds],ax
 mov ax,[cs:render_caller_psp]
 mov [cs:render_child_psp],ax
 mov word [cs:render_attached],1
 mov word [terminal_aspect_adopt],1
 xor ax,ax
 ret
.client_bad:
 add sp,4
 ret
.end:
 call terminal_script_window_close
 mov word [cs:render_attached],0
 xor ax,ax
 ret
.abort_confirm:
 cmp bx,4
 ja .operand
 cmp bx,3
 je .confirm_retire
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
.confirm_retire:
 ; A bounded drawing scope, with no child callback or parser entry.
 mov word [terminal_aspect_active],1
 call terminal_script_confirm
 mov word [terminal_aspect_active],0
 ret
.window_service:
 cmp bx,1
 ja .operand
 cmp word [_script_handoff+22],0
 jne .serial
 push bx
 call _aspect_render_admit
 pop bx
 or ax,ax
 jnz .done
 call terminal_script_window_service
 or ax,ax
 jnz .done
 call window_publish
 ret
.state:
 mov ax,10
 ret
.operand:
 mov ax,7
 ret

window_publish:
 mov bx,[cs:terminal_script_window_cooperative]
 mov ax,11
 call resident_bridge_callback
 cmp ax,14
 jbe .done
 mov ax,10
.done:
 ret

render_proxy:
 call far [cs:render_callback]
 retf
; Local keyboard/window polling is a separate foreground lifetime. Keep raw
; input in the child's ring and service flow without stealing Escape or using
; the parser continuation's72-tick/4096-operation rendering budget.
terminal_script_window_poll:
 cmp word [terminal_aspect_active],1
 jne .bad
 cmp word [cs:render_attached],1
 jne .bad
 xor bx,bx
 mov ax,10
 call resident_bridge_callback
 cmp ax,14
 jbe .done
.bad:
 mov ax,10
.done:
 ret

render_tick:
 push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 pop es
 ret
render_scope_end:
 mov word [terminal_aspect_active],0
 mov ax,[cs:render_saved_parser]
 mov [terminal_parser_active],ax
 mov ax,[cs:render_saved_wait]
 mov [terminal_ansi_wait_active],ax
 ret

; These exits are valid only during a captured body call on the parent stack.
terminal_render_unsupported:
 mov [cs:render_unsupported],ax
 mov ax,3
terminal_render_typed_abort:
 push ax
 call render_scope_end
 pop ax
 jmp resident_bridge_abort

; AX=callback request/BX=value. Restore caller registers except AX. Each raw
; result is checked against the child's typed error state before native use.
render_rpc:
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 cmp word [terminal_aspect_active],1
 jne .state
 cmp word [cs:render_remaining],0
 je .budget
 dec word [cs:render_remaining]
 mov si,ax
 call render_tick
 sub ax,[cs:render_started]
 cmp ax,72
 jae .budget
 mov ax,si
 call resident_bridge_callback
 cmp si,0
 je .raw
 cmp si,5
 je .raw
 or ax,ax
 jnz .error
 jmp .done
.raw:
 push ax
 mov ax,4
 call resident_bridge_callback
 or ax,ax
 jnz .error
 pop ax
 cmp ax,255
 jbe .done
 cmp ax,0xffff
 jne .state
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
.error:
 cmp ax,14
 jbe terminal_render_typed_abort
.state:
 mov ax,10
 jmp terminal_render_typed_abort
.budget:
 mov ax,6
 jmp terminal_render_typed_abort

terminal_render_read:
 xor ax,ax
 call render_rpc
 retf
terminal_render_read_now:
 mov ax,5
 call render_rpc
 retf
terminal_render_unread:
 mov ax,1
 call render_rpc
 retf
terminal_render_send:
 push ax
 push bx
 mov bx,ax
 and bx,255
 mov ax,2
 call render_rpc
 pop bx
 pop ax
 retf
terminal_render_poll:
terminal_render_cancel:
 mov ax,3
 call render_rpc
 retf
terminal_render_control:
 push ax
 call _aspect_render_preflight_control
 add sp,2
 or ax,ax
 jnz terminal_render_typed_abort
 retf
terminal_render_set_modes:
 mov ax,1
 jmp render_modes
terminal_render_reset_modes:
 xor ax,ax
render_modes:
 push ax
 call _aspect_render_preflight_modes
 add sp,2
 or ax,ax
 jnz terminal_render_typed_abort
 retf
terminal_render_string:
 push si
 push bx
 push cx
 mov si,ax
 mov bx,ax
 mov cx,1024
.bound:
 cmp byte [bx],0
 je .send
 inc bx
 jz .bad
 loop .bound
.bad:
 mov ax,7
 jmp terminal_render_typed_abort
.send:
 lodsb
 or al,al
 jz .done
 xor ah,ah
 call far terminal_render_send
 jmp .send
.done:
 pop cx
 pop bx
 pop si
 retf

render_attached: dw 0
render_token: dw 0
render_callback: dd 0
render_child_ds: dw 0
render_child_psp: dw 0
render_caller_ds: dw 0
render_caller_psp: dw 0
render_saved_parser: dw 0
render_saved_wait: dw 0
render_started: dw 0
render_remaining: dw 0
render_unsupported: dw 0
%ifdef ASPECT_EXTERNAL_RENDER
global render_program_owned,render_program_begins,render_program_ends,render_program_refreshes
render_program_owned: dw 0
render_program_begins: dw 0
render_program_ends: dw 0
render_program_refreshes: dw 0
%endif

SEGMENT _DATA public class=DATA use16
global terminal_aspect_active,terminal_aspect_adopt
global terminal_script_label_valid,terminal_script_label
terminal_script_label_valid: dw 0
terminal_script_label: times 13 db 0
terminal_aspect_active: dw 0
terminal_aspect_adopt: dw 0
