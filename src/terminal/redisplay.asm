; Serviced maintained redisplay. Only the top-level receive owner swaps frames;
; native parsing/capture/history continue against the real live display.
BITS 16
CPU 8086
%include "ui_storage.inc"
%ifdef TERMINAL_NATIVE_RESET_OVERLAY
%define REDISPLAY_SCREEN_OWNER_GUARD
%elifdef TERMINAL_DIRECTORY_VIEW
%define REDISPLAY_SCREEN_OWNER_GUARD
%endif
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
%ifdef TERMINAL_CHAT_STORAGE
extern _redisplay_live_ready,_redisplay_export_pending,_redisplay_search_pending
%endif
extern _command_menu_action,_command_menu_active
extern terminal_deferred_count,terminal_deferred_head,terminal_deferred_tail
extern terminal_history_pointer,terminal_history_start,terminal_history_end,terminal_history_wrapped
extern terminal_parser_active,terminal_transfer_pending,terminal_transfer_active
extern terminal_program_pending,terminal_program_active,terminal_macro_active
extern terminal_monitor_active,terminal_controller_active,terminal_ansi_wait_active
extern terminal_snapshot_active,uart_break_hold
extern screen_viewport_enabled,text_cga_status_port,text_video_segment
extern screen_attribute_row_bytes,screen_video_row_bytes,connection_state
extern terminal_viewport_admit_far

terminal_redisplay_key_impl:
%ifdef TERMINAL_EXTERNAL_VIEWER
 cmp ax,0xf300 ; F600 remains the browser's redial action.
 jne .not_external_viewer
 extern _viewer_external_start
 call far _viewer_external_start
 stc
 ret
.not_external_viewer:
%endif
 cmp word [_redisplay_active],0
 jne .key
%ifdef TERMINAL_GATEWAY
 extern terminal_gateway_key_far
 call far terminal_gateway_key_far
 jc .gateway_consumed
%endif
%ifdef TERMINAL_REFERENCE
 extern _command_reference_unavailable
 push ax
 push ax
 call far _command_reference_unavailable
 add sp,2
 or ax,ax
 pop ax
 jnz .open
 cmp al,'`'
 je .open
 cmp ax,0x6c00 ; Original Alt-F5: source-owned script filename prompt.
 je .open
%ifdef TERMINAL_FILE_DIRECTORY
 cmp ax,0x2100 ; Original Alt-F: serviced file listing.
 je .open
%endif
%ifdef TERMINAL_FILE_VIEWER
 cmp ax,0x2f00 ; Original Alt-V: serviced internal file viewer.
 je .open
%endif
%ifdef TERMINAL_EXTERNAL_EDITOR
 cmp ax,0x1e00 ; Original Alt-A: configured external editor.
 je .open
%endif
%ifdef TERMINAL_PATH_CONTROL
 cmp ax,0x6e00 ; Original Alt-F7: serviced path change.
 je .open
%endif
 cmp ax,0x1700 ; Original Alt-I: authored application information.
 je .open
%ifdef TERMINAL_DIRECTORY_VIEW
 cmp ax,0x2000 ; Serviced read-only directory; no redial or selection mutation.
 je .open
%endif
%endif
%ifdef TERMINAL_ELAPSED_VIEW
 cmp ax,0x1400 ; Guard/defer before the serviced viewer consumes this key.
 jne .not_elapsed
 extern terminal_local_control_key
 push ax
 call far terminal_local_control_key
 pop ax
 jc .elapsed_consumed
 jmp .open
.elapsed_consumed:
 stc
 ret
.not_elapsed:
%endif
 cmp ax,0x2c00 ; Alt-Z, maintained command menu and contextual help.
 je .open
%ifdef TERMINAL_ORIGINAL_KEYS
 cmp ax,0x1300 ; Original Alt-R: checked recorder dialog through this owner.
 je .open
 cmp ax,0x6d00 ; Original Alt-F6: redisplay.
 je .open
%endif
 cmp ax,0x8300 ; Alt-=, local filename clipboard.
 je .open
 cmp ax,0x8400 ; Ctrl-PgUp, local redisplay.
 je .open
 cmp ax,0x84e0
 jne .pass
.open:
 push ax
%ifdef REDISPLAY_SCREEN_OWNER_GUARD
 extern terminal_browser_screen_owned,terminal_editor_screen_owned
 cmp byte [terminal_browser_screen_owned],0
 jne .denied
 cmp byte [terminal_editor_screen_owned],0
 jne .denied
%endif
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
 or ax,[text_cga_status_port]
 jnz .denied
 cmp word [text_video_segment],0xb800
 jne .denied
 cmp word [screen_attribute_row_bytes],132
 je .wide
 cmp word [screen_attribute_row_bytes],80
 jne .denied
 cmp word [screen_viewport_enabled],0
 jne .denied
 jmp .physical
.wide:
 call far terminal_viewport_admit_far
 jc .denied
.physical:
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
%ifdef TERMINAL_CHAT_STORAGE
 pop ax
 cmp ax,0xffff ; Private acquire continuation, never a synthetic BIOS key.
 je .chat_claimed
 push ax
%endif
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
%ifdef TERMINAL_CHAT_STORAGE
.chat_claimed:
 mov word [_redisplay_active],2
 clc
 ret
%endif
.denied:
 pop ax
 stc
 ret
.key:
%ifdef TERMINAL_CHAT_STORAGE
%ifdef TERMINAL_CHAT_ECHO
 cmp word [_redisplay_active],2
 jne .viewer_key
 ; A busy Chat callback retains executable storage but must let the existing
 ; parent cancellation paths run. Do not consume their keys as viewer input.
 cmp ax,0x2d00
 je .ordinary
 cmp ax,0x2300
 je .ordinary
 cmp al,27
 je .ordinary
 jmp .refused
.viewer_key:
%else
 cmp word [_redisplay_active],2
 je .refused ; No viewer state exists for the Chat storage owner.
%endif
%endif
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
%ifdef TERMINAL_GATEWAY
.gateway_consumed:
 stc
 ret
%endif
global terminal_redisplay_key_end
terminal_redisplay_key_end:
%ifdef TERMINAL_CHAT_STORAGE
; Foreground-only FAR register API, DS=SS=parent, preserve all registers.
; CF0 acquired/retired, CF1 refused. Existing nonzero view-owner guards protect
; the complete frozen snapshot/index and live/view frames. No new near state.
; A caller must close/retire its own module before explicit release. Stop and
; ordinary keys cannot silently free executable storage or enter viewer C.
global terminal_chat_storage_acquire,terminal_chat_storage_release
terminal_chat_storage_acquire:
 push ax
 mov ax,[_redisplay_active]
 or ax,[_redisplay_live_ready]
 or ax,[_redisplay_export_pending]
 or ax,[_redisplay_search_pending]
 or ax,[_command_menu_active]
 jnz .denied
 cmp word [screen_attribute_row_bytes],80
 jne .denied
 mov ax,0xffff
 call terminal_redisplay_key_impl.open
 pop ax
 retf
.denied:
 pop ax
 stc
 retf
terminal_chat_storage_release:
 cmp word [_redisplay_active],2
 jne .denied
 mov word [_redisplay_active],0
 clc
 retf
.denied:
 stc
 retf
%ifdef TERMINAL_CHAT_REDISPLAY
; The foreground frontend has redirected the snapshot to an owned arena and
; saved its normal underlay. Reuse the full existing viewer admission/cleanup.
global _chat_view_enter,_chat_view_leave
_chat_view_enter:
 mov ax,0x6d00
 call terminal_redisplay_key_impl.open
 retf
_chat_view_leave:
 mov dx,4
 call redisplay_event
 retf
%endif
%endif
terminal_redisplay_before_impl:
 mov dx,2
 jmp redisplay_event
terminal_redisplay_idle_impl:
%ifdef TERMINAL_CHAT_FRONTEND
 extern terminal_chat_idle_far
 call far terminal_chat_idle_far
%ifdef TERMINAL_CHAT_REDISPLAY
 jnc .viewer_ready
 ret ; A held Chat presentation also suspends the viewer's paint continuation.
.viewer_ready:
%endif
%endif
 mov dx,3
 jmp redisplay_event
terminal_redisplay_stop_impl:
%ifdef TERMINAL_CHAT_FRONTEND
 extern terminal_chat_stop_far
 call far terminal_chat_stop_far
%endif
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
%ifdef TERMINAL_CHAT_STORAGE
 cmp word [_redisplay_active],2
 je .done ; Explicit owner retirement only, including foreground stop.
%endif
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
%ifdef TERMINAL_LARGE_VIEW_FRAMES
global terminal_large_view_frames
terminal_large_view_frames equ 1
%define VIEW_FRAME_BYTES 8000
%else
%define VIEW_FRAME_BYTES 4000
%endif
redisplay_live: resb VIEW_FRAME_BYTES
redisplay_live_end:
%ifdef TERMINAL_UI_SCREEN_OVERLAY
; Directory editing is synchronous inside the chooser. Bidirectional owner
; checks prevent it and the serviced viewer from borrowing this frame at once.
global ed_screen,ed_screen_end
ed_screen equ redisplay_live
ed_screen_end equ redisplay_live+4000 ; Synchronous editor retains its25-row contract.
%endif
redisplay_view: resb VIEW_FRAME_BYTES
redisplay_view_end:
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
; Last allocation in this variant. A quiesced child may borrow only this
; inactive snapshot/index; the distinct live ring remains retained throughout.
SEGMENT REDISPLAY_STORAGE public align=16 class=FROZEN_DATA use16
%else
SEGMENT REDISPLAY_STORAGE public align=16 class=FAR_DATA use16
%endif
global redisplay_snapshot,redisplay_snapshot_end
redisplay_snapshot: resb 63000
redisplay_snapshot_end:
%ifdef TERMINAL_DIRECTORY_STORAGE
; Alt-G is synchronous and refuses an active viewer/command owner. The viewer
; already refuses terminal_snapshot_active. Inactive frozen history is rebuilt
; from the separate63000-byte live ring on every opening; its tail can lend a
; complete2000-byte character image without reducing any role's capacity.
global terminal_snapshot_image,terminal_snapshot_image_end
terminal_snapshot_image equ redisplay_snapshot+61000
terminal_snapshot_image_end equ redisplay_snapshot_end
%endif
; The row index is used only by the far-aware C viewer, never as a near DOS
; buffer. Keep it beside the retained snapshot, outside the DS=SS group.
global _redisplay_row_index,_redisplay_row_index_end
_redisplay_row_index: resw 247
_redisplay_row_index_end:
extern terminal_history_buffer
