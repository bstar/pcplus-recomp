; Small maintained connection notice using the recovered window services.
; SI=NUL string of at most14 bytes. No delay/keyboard/serial service is called.
; The first15 bottom-row cells are restored before online data is rendered.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern pcplus_screen_save,pcplus_screen_restore,pcplus_flow_message
extern terminal_redisplay_stop
global terminal_connection_notice,terminal_connection_notice_restore
extern terminal_status_live
extern ui_flow_suppressed,ui_flow_region_cells,ui_flow_video_base,ui_flow_coordinate_base
extern screen_columns,screen_video_row_bytes,text_video_segment
%ifdef TERMINAL_SCREEN_PAUSE
%define TERMINAL_MODAL_NOTICE
extern terminal_screen_pause_active
%endif
%ifdef TERMINAL_ELAPSED_VIEW
%define TERMINAL_MODAL_NOTICE
extern _terminal_elapsed_view_active
%endif
%ifdef TERMINAL_MODAL_NOTICE
global terminal_pause_notice_flush_far
%endif
global terminal_status_notice_refresh
%macro save 0
 push bp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 ret
%endmacro
terminal_connection_notice:
 save
%ifdef TERMINAL_MODAL_NOTICE
%ifdef TERMINAL_ELAPSED_VIEW
%ifdef TERMINAL_SCREEN_PAUSE
 cmp word [terminal_screen_pause_active],0
 jne .deferred
%endif
 cmp word [_terminal_elapsed_view_active],0
 jne .deferred
 jmp .not_paused
.deferred:
%else
 cmp word [terminal_screen_pause_active],0
 je .not_paused
%endif
 mov [pause_notice_text],si
 mov word [pause_notice_action],1
 jmp .done
.not_paused:
%endif
 ; Canonical suppression releases this row to terminal output. Never acquire
 ; an underlay there, even if a previous notice is still marked active.
 call notice_row_admit
 jc .discard
 ; Notices own the live screen, never a cached history-page underlay.
 call terminal_redisplay_stop
 cmp byte [notice_active],0
 jne .draw
 mov ax,notice_cells
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_save
 mov byte [notice_active],1
.draw:
 xor ax,ax
 push ax
 push si
 call pcplus_flow_message
 add sp,4
 jmp .done
.discard:
 mov byte [notice_active],0
.done:
 restore
terminal_connection_notice_restore:
 save
%ifdef TERMINAL_MODAL_NOTICE
%ifdef TERMINAL_ELAPSED_VIEW
%ifdef TERMINAL_SCREEN_PAUSE
 cmp word [terminal_screen_pause_active],0
 jne .deferred
%endif
 cmp word [_terminal_elapsed_view_active],0
 jne .deferred
 jmp .not_paused
.deferred:
%else
 cmp word [terminal_screen_pause_active],0
 je .not_paused
%endif
 mov word [pause_notice_action],2
 jmp .done
.not_paused:
%endif
 cmp byte [notice_active],0
 je .done
 ; A geometry owner must retire a notice before releasing its row. If that
 ; contract was missed, discard the stale lease rather than erase newer RX.
 call notice_row_admit
 jc .discard
 mov ax,notice_cells
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_restore
.discard:
 mov byte [notice_active],0
.done:
 restore

%ifdef TERMINAL_MODAL_NOTICE
; Pause owns the full status row. Preserve the latest real notice/restore
; transition without capturing its prompt as the connection notice underlay.
; Called only after Pause restores that row and releases its ownership flag.
terminal_pause_notice_flush_far:
 push si
 mov ax,[pause_notice_action]
 mov word [pause_notice_action],0
 cmp ax,1
 je .notice
 cmp ax,2
 jne .done
 call terminal_connection_notice_restore
 jmp .done
.notice:
 mov si,[pause_notice_text]
 call terminal_connection_notice
.done:
 pop si
 retf
%endif

; CONFIG caller's far frame. Preserve the live fifteen-cell notice while
; refreshing its underlay and the rest of the native status row. The temporary
; video copy is on the ordinary DS=SS stack, with no persistent borrowed pointer.
terminal_status_notice_refresh:
 push bp
 mov bp,sp
 sub sp,32
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call notice_row_admit
 jnc .admitted
 mov byte [notice_active],0
 mov word [bp-32],3 ; Same unsupported-geometry result as STATUS.
 jmp .done
.admitted:
 cmp byte [notice_active],0
 je .draw
 lea ax,[bp-30]
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_save
.draw:
 mov bx,0xffff
 call far terminal_status_live
 mov [bp-32],ax
 cmp byte [notice_active],0
 je .done
 or ax,ax
 jnz .restore_notice
 mov ax,notice_cells
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_save
.restore_notice:
 lea ax,[bp-30]
 push ax
 mov ax,3840
 push ax
 mov ax,15
 push ax
 call pcplus_screen_restore
.done:
 mov ax,[bp-32]
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf

; Read-only admission for the existing fixed physical row25 lease. This does
; not authorize a new geometry or probe BIOS; callers retain that responsibility.
; Keep AX and all other registers intact, returning only CF.
notice_row_admit:
 cmp word [ui_flow_suppressed],0
 jne .bad
 cmp word [ui_flow_region_cells],80
 jne .bad
 cmp word [ui_flow_video_base],3840
 jne .bad
 cmp word [ui_flow_coordinate_base],0x1800
 jne .bad
 cmp word [screen_columns],80
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [text_video_segment],0xb800
 jne .bad
 clc
 ret
.bad:
 stc
 ret
; Shared read-only gate for owners which require the reserved status row.
; Geometry/BIOS and all other owner checks remain at the requesting service.
global terminal_status_row_admit_far
terminal_status_row_admit_far:
 call notice_row_admit
 retf
SEGMENT _DATA public class=DATA use16
notice_active: db 0
notice_cells: times 30 db 0
%ifdef TERMINAL_MODAL_NOTICE
pause_notice_text: dw 0
pause_notice_action: dw 0
%endif
