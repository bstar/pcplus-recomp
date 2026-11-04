; Maintained foreground integration of the recovered DD7E Screen Pause contract.
; Keep the original XOFF -> hide/save/message -> consume one key -> restore/XON
; ordering. UART control delivery is queued/bounded, never a THRE/CTS spin.
BITS 16
CPU 8086
%ifdef TERMINAL_SCREEN_PAUSE
SEGMENT _TEXT public class=CODE use16
extern uart_flow_pending,uart_poll_flow,terminal_poll_serial,keyboard_poll,terminal_read_key
global terminal_pause_flow_far,terminal_pause_poll_far,terminal_pause_peek_far,terminal_pause_read_far
terminal_pause_flow_far:
 mov [uart_flow_pending],al
 call uart_poll_flow
 retf
terminal_pause_poll_far:
 call terminal_poll_serial
 retf
terminal_pause_peek_far:
 call keyboard_poll
 retf
terminal_pause_read_far:
 call terminal_read_key
 retf

SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern terminal_quit,terminal_deferred_count
extern terminal_pause_notice_flush_far
extern terminal_status_row_admit_far
extern text_video_segment,screen_video_row_bytes,screen_attribute_row_bytes,screen_viewport_enabled
extern terminal_local_control_status
%ifdef TERMINAL_ROW_GEOMETRY
extern _terminal_row_status_layout,ui_window_rows,ui_flow_video_base,ui_flow_suppressed,csi_column_count
extern terminal_exit_code
%endif
extern terminal_connection_flow_alive,terminal_connection_flow_ready
extern uart_flow_pending
; Logical lifetime retains a desired resume through a short DCD drop. The
; foreground readiness policy prevents output into modem command mode; a
; retired connection must not acquire a new pending control after cleanup.
global terminal_pause_control
terminal_pause_control:
 push ax
 call far terminal_connection_flow_alive
 or ax,ax
 jz .dead
 pop ax
 mov [uart_flow_pending],al
 push ax
 call far terminal_connection_flow_ready
 or ax,ax
 pop ax
 jz .done
 call far terminal_pause_flow_far
 ret
.dead:
 pop ax
.done:
 ret
global terminal_screen_pause,terminal_screen_pause_end
terminal_screen_pause:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov bp,sp
 cmp word [terminal_screen_pause_active],0
 jne .unsupported
 call pause_layout
 jc .unsupported
 sub sp,164 ; eighty cells, incoming shape, captured byte offset.
 mov [ss:bp-164],ax
 mov word [terminal_screen_pause_active],1
 mov al,0x13
 call terminal_pause_control
 mov ax,0x0300
 xor bx,bx
 int 0x10
 mov [ss:bp-2],cx
 or ch,0x20
 mov ax,0x0100
 int 0x10
 mov ax,0xb800
 mov es,ax
 mov si,[ss:bp-164]
 xor di,di
 mov cx,80
.save:
 mov ax,[es:si]
 mov [ss:bp+di-162],ax
 add si,2
 add di,2
 loop .save
 mov di,[ss:bp-164]
 mov ax,0x7020
 mov cx,80
 rep stosw
 mov di,[ss:bp-164]
 add di,(80-(.message_end-.message-1))/2*2
 mov si,.message
.draw:
 mov al,[cs:si]
 inc si
 or al,al
 jz .wait
 mov ah,0x70
 stosw
 jmp .draw
.wait:
 call far terminal_pause_poll_far
 cmp word [terminal_quit],0
 jne .resume
 cmp word [terminal_deferred_count],0
 jne .read
 call far terminal_pause_peek_far
 or ax,ax
 jz .wait
.read:
 call far terminal_pause_read_far ; Native behavior: even Esc/Alt-X only resumes.
.resume:
 call pause_layout
 jc .stale
 cmp ax,[ss:bp-164]
 jne .stale
 mov ax,0xb800
 mov es,ax
 mov di,[ss:bp-164]
 xor si,si
 mov cx,80
.restore:
 mov ax,[ss:bp+si-162]
 stosw
 add si,2
 loop .restore
 mov cx,[ss:bp-2]
 mov ax,0x0100
 int 0x10
 mov al,0x11
 call terminal_pause_control
 mov word [terminal_screen_pause_active],0
 call far terminal_pause_notice_flush_far
.finish:
 mov sp,bp
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret
.stale:
 ; Never replay a saved row or shape into a different display. Release the
 ; modal owner and request existing fatal shutdown instead of mixed parsing.
 mov word [terminal_screen_pause_active],0
 mov word [terminal_local_control_status],3
 mov word [terminal_quit],1
%ifdef TERMINAL_ROW_GEOMETRY
 cmp word [terminal_exit_code],0
 jne .finish
 mov word [terminal_exit_code],7
%endif
 jmp .finish
.unsupported:
 mov word [terminal_local_control_status],3
 jmp .finish
.message: db 'Screen paused.  Press any key to continue...',0
.message_end:
terminal_screen_pause_end:
; Pure admission before acquisition and replay; no persistent scratch. Return
; AX=reserved row byte offset, CF=0. Preserve the running modal stack/cursors.
pause_layout:
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov bx,ds
 mov cx,ss
 cmp bx,cx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
%ifdef TERMINAL_ROW_GEOMETRY
 cmp word [ui_flow_suppressed],0
 jne .bad
 call far _terminal_row_status_layout
 or ax,ax
 jnz .bad
 cmp word [csi_column_count],80
 jne .bad
%else
 call far terminal_status_row_admit_far
 jc .bad
%endif
 cmp word [text_video_segment],0xb800
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [screen_attribute_row_bytes],80
 jne .bad
 cmp word [screen_viewport_enabled],0
 jne .bad
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 or ax,ax
 jz .legacy25
 inc ax
 jmp .height
.legacy25:
 mov ax,25
.height:
%ifdef TERMINAL_ROW_GEOMETRY
 cmp ax,[ui_window_rows]
%else
 cmp ax,25
%endif
 jne .bad
 mov ax,0x0f00
 int 0x10
 cmp ah,80
 jne .bad
 cmp bh,0
 jne .bad
 and al,0x7f
 cmp al,2
 je .geometry_ok
 cmp al,3
 jne .bad
.geometry_ok:
%ifdef TERMINAL_ROW_GEOMETRY
 mov ax,[ui_flow_video_base]
%else
 mov ax,3840
%endif
 clc
 jmp .done
.bad:
 stc
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
SEGMENT _DATA public class=DATA use16
global terminal_screen_pause_active
terminal_screen_pause_active: dw 0
%endif
