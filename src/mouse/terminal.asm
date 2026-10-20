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
FAR_CDECL_ENTRY _terminal_mouse_stage,2
FAR_CDECL_ENTRY _terminal_mouse_offer,2
FAR_CDECL_ENTRY _terminal_mouse_commit,0
FAR_CDECL_ENTRY _terminal_mouse_discard,0
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
 call _terminal_mouse_stop_impl
 or ax,ax
 jz .released
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
 mov dx,[process_keep_paragraphs]
 mov ax,0x310e
 int 0x21
.released:
 retf
retained_message: db 13,10,'Mouse restore failed; application memory retained.',13,10,'$'
%endif
