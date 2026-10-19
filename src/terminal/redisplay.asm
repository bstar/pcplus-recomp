; Serviced maintained redisplay. Only the top-level receive owner swaps frames;
; native parsing/capture/history continue against the real live display.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
NEAR_ENTRY terminal_redisplay_key
NEAR_ENTRY terminal_redisplay_before
NEAR_ENTRY terminal_redisplay_idle
NEAR_ENTRY terminal_redisplay_stop
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global terminal_redisplay_key_impl,terminal_redisplay_before_impl,terminal_redisplay_idle_impl,terminal_redisplay_stop_impl
FAR_ENTRY terminal_redisplay_key
FAR_ENTRY terminal_redisplay_before
FAR_ENTRY terminal_redisplay_idle
FAR_ENTRY terminal_redisplay_stop

extern _redisplay_event_impl,_redisplay_active
extern _command_menu_action,_command_menu_active
extern terminal_deferred_count,terminal_deferred_head,terminal_deferred_tail
extern terminal_history_pointer,terminal_history_start,terminal_history_end,terminal_history_wrapped
extern terminal_parser_active,terminal_transfer_pending,terminal_transfer_active
extern terminal_program_pending,terminal_program_active,terminal_macro_active
extern terminal_monitor_active,terminal_controller_active,terminal_ansi_wait_active
extern terminal_snapshot_active,uart_break_hold
extern screen_viewport_enabled,text_cga_status_port,text_video_segment
extern screen_attribute_row_bytes,screen_video_row_bytes,connection_state

terminal_redisplay_key_impl:
 cmp word [_redisplay_active],0
 jne .key
 cmp ax,0x2c00 ; Alt-Z, maintained command menu and contextual help.
 je .open
 cmp ax,0x8300 ; Alt-=, local filename clipboard.
 je .open
 cmp ax,0x8400 ; Ctrl-PgUp, local redisplay.
 je .open
 cmp ax,0x84e0
 jne .pass
.open:
 push ax
 mov ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 or ax,[terminal_macro_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[terminal_snapshot_active]
 or ax,[uart_break_hold]
 or ax,[screen_viewport_enabled]
 or ax,[text_cga_status_port]
 jnz .denied
 cmp word [text_video_segment],0xb800
 jne .denied
 cmp word [screen_attribute_row_bytes],80
 jne .denied
 cmp word [screen_video_row_bytes],160
 jne .denied
 cmp word [connection_state],0
 je .parser
 cmp word [connection_state],6
 jne .denied
.parser:
 cmp word [terminal_parser_active],0
 je .bind
 pop ax
 cmp ax,0x2c00
 jne .refused
 ; Only an otherwise eligible Alt-Z is deferred. Other viewer keys retain
 ; their existing refusal policy, and other owners never become menu requests.
 mov word [terminal_menu_pending],1
.refused:
 stc
 ret
.bind:
 mov ax,[terminal_history_start]
 mov [context+16],ax
 mov ax,[terminal_history_end]
 mov [context+18],ax
 mov ax,[terminal_history_pointer]
 mov [context+20],ax
 mov ax,[terminal_history_wrapped]
 mov [context+22],ax
 pop ax
 xor dx,dx
 jmp .call
.denied:
 pop ax
 stc
 ret
.key:
 mov dx,1
.call:
 push ax
 push bp
 push si
 push di
 push es
 mov bx,context
 push bx
 push ax
 push dx
 call _redisplay_event_impl
 add sp,6
 or ax,ax
 pop es
 pop di
 pop si
 pop bp
 pop ax
 jz .pass
 stc
 ret
.pass:
 cmp word [_command_menu_action],0
 je .ordinary
 mov ax,[_command_menu_action]
 mov word [_command_menu_action],0
 ; Redispatch only after the old view has restored the live screen. Viewer
 ; commands acquire their normal guarded owner; other commands return to the
 ; existing transport dispatcher. No synthetic key reaches the BIOS/UART.
 jmp terminal_redisplay_key_impl
.ordinary:
 clc
 ret
terminal_redisplay_before_impl:
 mov dx,2
 jmp redisplay_event
terminal_redisplay_idle_impl:
 mov dx,3
 jmp redisplay_event
terminal_redisplay_stop_impl:
 cmp word [terminal_menu_pending],0
 jne .cancel
 cmp word [_command_menu_active],0
 je .event
.cancel:
 mov word [terminal_menu_pending],0
 mov word [terminal_deferred_count],0
 mov word [terminal_deferred_head],0
 mov word [terminal_deferred_tail],0
.event:
 mov dx,4
redisplay_event:
 cmp word [_redisplay_active],0
 je .done
 push ax
 push bp
 push si
 push di
 push es
 mov ax,context
 push ax
 xor ax,ax
 push ax
 push dx
 call _redisplay_event_impl
 add sp,6
 pop es
 pop di
 pop si
 pop bp
 pop ax
.done:
 ret
SEGMENT _DATA public class=DATA use16
global redisplay_live_segment,redisplay_view_segment,redisplay_snapshot_segment
redisplay_live_segment equ context+10
redisplay_view_segment equ context+14
redisplay_snapshot_segment equ context+6
context:
 dw 0,seg terminal_history_buffer
 dw redisplay_snapshot,seg redisplay_snapshot
 dw redisplay_live,seg redisplay_live
 dw redisplay_view,seg redisplay_view
 times 4 dw 0
global terminal_menu_pending
terminal_menu_pending: dw 0
SEGMENT UI_STORAGE public align=16 class=FAR_DATA use16
global redisplay_live,redisplay_live_end,redisplay_view,redisplay_view_end
redisplay_live: resb 4000
redisplay_live_end:
redisplay_view: resb 4000
redisplay_view_end:
SEGMENT REDISPLAY_STORAGE public align=16 class=FAR_DATA use16
global redisplay_snapshot,redisplay_snapshot_end
redisplay_snapshot: resb 63000
redisplay_snapshot_end:
; The row index is used only by the far-aware C viewer, never as a near DOS
; buffer. Keep it beside the retained snapshot, outside the DS=SS group.
global _redisplay_row_index,_redisplay_row_index_end
_redisplay_row_index: resw 247
_redisplay_row_index_end:
extern terminal_history_buffer
