; Shared real terminal renderer, retained across a checked ASPECT child lease.
; Application policy lives in ASPECT_CODE; small resident adapters retain the
; native near/cdecl ABIs. No capability is published until script prepare.
BITS 16
CPU 8086
%include "resident_bridge.inc"
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
 mov word [_script_render_version],4
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
 ; Parent cursor cleanup needs no retired child callback or UART operation.
 push bx
 mov bx,1
 call far terminal_break_ui
 pop bx
 call resident_bridge_disable
 mov word [cs:render_attached],0
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
 cmp word [_script_render_version],4
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
 cmp di,1
 jne .state
 cmp bx,255
 ja .operand
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
 call far terminal_status_live
 ret
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
 call far terminal_break_ui
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
 mov word [cs:render_attached],0
 xor ax,ax
 ret
.state:
 mov ax,10
 ret
.operand:
 mov ax,7
 ret

render_proxy:
 call far [cs:render_callback]
 retf
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

SEGMENT _DATA public class=DATA use16
global terminal_aspect_active,terminal_aspect_adopt
global terminal_script_label_valid,terminal_script_label
terminal_script_label_valid: dw 0
terminal_script_label: times 13 db 0
terminal_aspect_active: dw 0
terminal_aspect_adopt: dw 0
