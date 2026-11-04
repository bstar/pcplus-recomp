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
 call far terminal_status_row_admit_far
 jc .unsupported
 cmp word [text_video_segment],0xb800
 jne .unsupported
 cmp word [screen_video_row_bytes],160
 jne .unsupported
 cmp word [screen_attribute_row_bytes],80
 jne .unsupported
 cmp word [screen_viewport_enabled],0
 jne .unsupported
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x84],24
 jne .unsupported
 mov ax,0x0f00
 int 0x10
 cmp ah,80
 jne .unsupported
 cmp bh,0
 jne .unsupported
 and al,0x7f
 cmp al,2
 je .geometry_ok
 cmp al,3
 jne .unsupported
.geometry_ok:
 cld
 sub sp,162 ; eighty cells, followed by the exact incoming BIOS cursor shape.
 mov word [terminal_screen_pause_active],1
 mov al,0x13
 call far terminal_pause_flow_far
 mov ax,0x0300
 xor bx,bx
 int 0x10
 mov [ss:bp-2],cx
 or ch,0x20
 mov ax,0x0100
 int 0x10
 mov ax,0xb800
 mov es,ax
 mov si,3840
 xor di,di
 mov cx,80
.save:
 mov ax,[es:si]
 mov [ss:bp+di-162],ax
 add si,2
 add di,2
 loop .save
 mov di,3840
 mov ax,0x7020
 mov cx,80
 rep stosw
 mov di,3840+(80-(.message_end-.message-1))/2*2
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
 mov di,3840
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
 call far terminal_pause_flow_far
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
.unsupported:
 mov word [terminal_local_control_status],3
 jmp .finish
.message: db 'Screen paused.  Press any key to continue...',0
.message_end:
terminal_screen_pause_end:
SEGMENT _DATA public class=DATA use16
global terminal_screen_pause_active
terminal_screen_pause_active: dw 0
%endif
