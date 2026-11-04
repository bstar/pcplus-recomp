; Foreground lifecycle, CONFIG->mouse staging and resident keyboard callbacks.
BITS 16
CPU 8086
%include "far_bridge.inc"
%ifdef TERMINAL_MOUSE
SEGMENT _TEXT public class=CODE use16
%macro terminal_mouse_entry 1
 NEAR_CDECL_ENTRY %1,0
%endmacro
terminal_mouse_entry _terminal_mouse_bootstrap
terminal_mouse_entry _terminal_mouse_start
terminal_mouse_entry _terminal_mouse_pause
terminal_mouse_entry _terminal_mouse_resume
NEAR_NAMED_SERVICE mouse_keyboard_poll,keyboard_poll
NEAR_NAMED_SERVICE mouse_keyboard_read,keyboard_read
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
NEAR_CDECL_ENTRY _terminal_mouse_stage,2
NEAR_CDECL_ENTRY _terminal_mouse_offer,2
NEAR_CDECL_ENTRY _terminal_mouse_commit,0
NEAR_CDECL_ENTRY _terminal_mouse_discard,0
SEGMENT MOUSE_CODE public align=16 class=FARCODE use16
GROUP MOUSE_GROUP MOUSE_CODE
global terminal_mouse_code_start
terminal_mouse_code_start:
FAR_CDECL_ENTRY _terminal_mouse_bootstrap,0
FAR_CDECL_ENTRY _terminal_mouse_start,0
FAR_CDECL_ENTRY _terminal_mouse_pause,0
FAR_CDECL_ENTRY _terminal_mouse_resume,0
%ifdef TERMINAL_ROW_GEOMETRY
extern _mouse_owner_phase_impl
extern mouse_bind,mouse_button_pending,_terminal_mouse_resume_impl
global terminal_rows_mouse_phase_far,terminal_rows_mouse_resume_far,terminal_rows_mouse_bind
terminal_rows_mouse_phase_far:
 call _mouse_owner_phase_impl
 retf
; The driver is suspended. Preserve only already-encoded native keyboard input;
; fresh mickey baselines must remain reset for the driver's new video geometry.
terminal_rows_mouse_resume_far:
 push bx
 push cx
 push si
 push di
 mov si,mouse_button_pending
 mov di,row_saved_pending
 mov cx,3
.save:
 mov ax,[si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .save
 mov word [cs:row_resume_pending],1
 call _terminal_mouse_resume_impl
 mov word [cs:row_resume_pending],0
 pop di
 pop si
 pop cx
 pop bx
 retf
; Used only as native INIT's bind target in this experimental geometry build.
; Restore queued Enter/Escape/repeat input before the callback is installed.
; No foreground store can then overwrite an event from the newly live callback.
terminal_rows_mouse_bind:
 pushf
 cmp word [cs:row_resume_pending],0
 je .bind
 push ax
 push cx
 push si
 push di
 mov si,row_saved_pending
 mov di,mouse_button_pending
 mov cx,3
.restore:
 mov ax,[cs:si]
 mov [di],ax
 add si,2
 add di,2
 loop .restore
 pop di
 pop si
 pop cx
 pop ax
.bind:
 popf
 jmp mouse_bind
row_resume_pending: dw 0
row_saved_pending: times 3 dw 0
%endif
FAR_CDECL_ENTRY _terminal_mouse_stage,2
FAR_CDECL_ENTRY _terminal_mouse_offer,2
FAR_CDECL_ENTRY _terminal_mouse_commit,0
FAR_CDECL_ENTRY _terminal_mouse_discard,0
%ifdef TERMINAL_HOOK_APPLY
FAR_CDECL_ENTRY _terminal_mouse_check,0
FAR_CDECL_ENTRY _terminal_mouse_publish,0
%endif
extern process_psp,process_keep_paragraphs,process_minimum_paragraphs,process_memory_released
global _mouse_terminal_release_unused,terminal_mouse_exit
_mouse_terminal_release_unused:
 push bx
 push es
 cmp word [process_memory_released],1
 je .success
 mov ax,[process_psp]
 or ax,ax
 jz .invalid
 mov es,ax
 mov bx,[process_keep_paragraphs]
 cmp bx,0x10
 jb .invalid
 cmp word [process_minimum_paragraphs],0x10
 jb .invalid
 cmp bx,[process_minimum_paragraphs]
 jb .invalid
 mov ah,0x4a
 int 0x21
 jc .done
 mov word [process_memory_released],1
.success:
 xor ax,ax
 jmp short .done
.invalid:
 mov ax,1
.done:
 pop es
 pop bx
 ret

extern _terminal_mouse_stop_impl
terminal_mouse_exit:
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 extern _mouse_platform_strategy_finish
 call _mouse_platform_strategy_finish
 or ax,ax
 jnz .retain
%endif
 call _terminal_mouse_stop_impl
 or ax,ax
 jz .released
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
.retain:
%endif
 ; Cleanup of UART/file/video owners has already completed. If an IRQ driver
 ; can still reference us, DOS4C would leave a dangling pointer. Keep the full
 ; checked static parent and its DOS48 blocks resident, returning typed error14.
 push ds
 push cs
 pop ds
 mov dx,retained_message
 mov ah,9
 int 0x21
 pop ds
%ifdef TERMINAL_TRAPS
 extern terminal_exit_guard_mouse_held
 call far terminal_exit_guard_mouse_held
%else
 mov dx,[process_keep_paragraphs]
 mov ax,0x310e
 int 0x21
%endif
.released:
 retf
retained_message: db 13,10,'Mouse restore failed; application memory retained.',13,10,'$'
%endif
