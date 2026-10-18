; Maintained media copy. Native E084/E2F8/E3CA remain exact diagnostics.
; Freeze physical characters through actual6FA0; share the private snapshot
; image only while this modal foreground owns it. Never trim/normalize bytes.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern ansi_parameter_count,ansi_parameters,ansi_private
extern modes_value_3980,modes_value_3982
extern terminal_snapshot_active,terminal_monitor_active
extern terminal_transfer_pending,terminal_transfer_active
extern terminal_macro_active,terminal_program_pending,connection_state
extern csi_row_count,csi_scroll_top,csi_scroll_bottom,screen_cursor_row
extern screen_columns,screen_video_row_bytes,screen_viewport_enabled
extern text_video_segment,text_cga_status_port,ui_read_byte
extern terminal_snapshot_image,terminal_snapshot_image_segment
extern terminal_connection_notice_restore,terminal_connection_notice
extern terminal_poll_serial,terminal_quit,terminal_exit_code,uart_rx_dropped
extern keyboard_poll,terminal_read_key,terminal_defer_key
extern _printer_device_begin,_printer_device_result
extern terminal_printer_count,terminal_printer_closing
extern terminal_printer_put_raw,terminal_printer_poll,terminal_printer_shutdown
extern terminal_sink_3988_enabled,terminal_printer_failure
extern terminal_printer_fault_epoch,terminal_abort
extern terminal_controller_run,terminal_controller_active,terminal_controller_last_action
global csi_media_copy,terminal_screen_print
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

csi_media_copy:
 save
 xor di,di
 cmp word [ansi_parameter_count],0
 je .selected
.next:
 mov bx,di
 shl bx,1
 mov ax,[ansi_parameters+bx]
 or ax,ax
 jz .selected
 cmp ax,1
 je .row
 cmp ax,4
 je .off
 cmp ax,5
 jne .advance
 cmp word [ansi_private],0
 je .controller
 ; Private5 is idempotent stream admission, not the dedicated controller.
 call screen_print_admit
 jc .denied
 mov word [terminal_sink_3988_enabled],1
 jmp .advance
.off:
 cmp word [ansi_private],0
 je .advance
 mov word [terminal_sink_3988_enabled],0
 cmp word [_printer_device_result+10],0
 je .advance
 mov word [terminal_printer_closing],1
 jmp .advance
.selected:
 mov ax,1
 cmp word [modes_value_3982],0
 je .print
 inc ax
 jmp .print
.row:
 mov ax,3
.print:
 call terminal_screen_print
.advance:
 inc di
 cmp di,[ansi_parameter_count]
 jb .next
 restore
.denied:
 cmp word [text_cga_status_port],0
 jne .advance
 mov si,screen_print_denied
 call terminal_connection_notice
 jmp .advance
.controller:
 call terminal_controller_run
 cmp word [terminal_quit],0
 jne .finished
 cmp word [terminal_controller_last_action],5
 jne .advance
.finished:
 restore

; AX1=full,2=scroll region,3=current row. Preserve all caller registers.
terminal_screen_print:
 save
 cmp word [terminal_screen_print_active],0
 jne .return
 mov word [terminal_screen_print_action],2
 mov word [terminal_screen_print_bytes],0
 cmp word [terminal_controller_active],0
 jne .return
 mov [screen_print_mode],ax
 call screen_print_geometry
 jc .return
 cmp word [terminal_snapshot_active],0
 jne .denied
 cmp word [terminal_monitor_active],0
 jne .denied
 cmp word [terminal_transfer_pending],0
 jne .denied
 cmp word [terminal_transfer_active],0
 jne .denied
 cmp word [terminal_macro_active],0
 jne .denied
 cmp word [terminal_program_pending],0
 jne .denied
 cmp word [connection_state],0
 je .rows
 cmp word [connection_state],6
 jne .denied
.rows:
 xor ax,ax
 mov dx,25
 cmp word [screen_print_mode],1
 je .bounds
 mov ax,[csi_scroll_top]
 mov dx,[csi_scroll_bottom]
 inc dx
 cmp word [screen_print_mode],2
 je .bounds
 cmp word [screen_print_mode],3
 jne .denied
 mov ax,[screen_cursor_row]
 mov dx,ax
 inc dx
.bounds:
 cmp ax,dx
 jae .denied
 cmp dx,25
 ja .denied
 mov [screen_print_row_end],dx
 mov bx,80
 mul bx
 mov [screen_print_position],ax
 mov ax,[terminal_printer_fault_epoch]
 mov [screen_print_epoch],ax
 mov word [terminal_screen_print_bytes],0
 mov word [terminal_screen_print_active],1
 mov word [screen_print_temporary],0
 call terminal_connection_notice_restore
 mov es,[terminal_snapshot_image_segment]
 mov di,terminal_snapshot_image
 xor si,si
.freeze:
 push si
 call ui_read_byte ;Near callee-clean2, preserves SI/DS; actual native reader.
 cld
 stosb
 add si,2
 cmp si,4000
 jb .freeze
 call screen_print_admit
 jc .admit_failed
 cmp word [terminal_sink_3988_enabled],0
 jne .output
 mov word [screen_print_temporary],1
.output:
 mov cx,80
.character:
 push cx
 mov es,[terminal_snapshot_image_segment]
 mov bx,[screen_print_position]
 mov al,[es:terminal_snapshot_image+bx]
 xor ah,ah
 call screen_print_put
 pop cx
 jc .canceled
 inc word [screen_print_position]
 loop .character
 mov ax,13
 call screen_print_put
 jc .canceled
 mov ax,10
 call screen_print_put
 jc .canceled
 mov ax,[screen_print_position]
 xor dx,dx
 mov bx,80
 div bx
 cmp ax,[screen_print_row_end]
 jb .output
 cmp word [screen_print_mode],3
 je .flush
 cmp word [modes_value_3980],0
 je .flush
 mov ax,12
 call screen_print_put
 jc .canceled
.flush:
 call screen_print_service
 jc .canceled
 cmp word [terminal_printer_count],0
 jne .flush
 mov word [terminal_screen_print_action],1
 jmp .finish
.admit_failed:
 mov word [terminal_screen_print_action],2
 jmp .finish
.canceled:
 mov word [terminal_screen_print_action],3
.finish:
 cmp word [screen_print_temporary],0
 je .status
 call terminal_printer_shutdown
.status:
 mov ax,[terminal_printer_fault_epoch]
 cmp ax,[screen_print_epoch]
 je .notice
 mov word [terminal_screen_print_action],4
.notice:
 mov word [terminal_screen_print_active],0
 mov bx,[terminal_screen_print_action]
 dec bx
 shl bx,1
 mov si,[screen_print_notices+bx]
 call terminal_connection_notice
 jmp .return
.denied:
 mov si,screen_print_denied
 call terminal_connection_notice
.return:
 restore

screen_print_geometry:
 cmp word [text_cga_status_port],0
 jne .bad
 cmp word [text_video_segment],0xb800
 jne .bad
 cmp word [screen_columns],80
 jne .bad
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [csi_row_count],25
 jne .bad
 cmp word [screen_viewport_enabled],0
 jne .bad
 mov ah,0x0f
 int 0x10
 cmp ax,0x5003
 jne .bad
 or bh,bh
 jnz .bad
 push es
 mov ax,0x40
 mov es,ax
 mov al,[es:0x84]
 pop es
 or al,al
 jz .ok
 cmp al,24
 jne .bad
.ok:
 clc
 ret
.bad:
 stc
 ret

; Checked shared PRN admission. Close/drain a preceding private4 before5.
; Failure from an unacquired open is UI-only; acquired failures stay sticky.
screen_print_admit:
 cmp word [terminal_printer_closing],0
 je .owner
 call terminal_printer_poll
 call terminal_poll_serial
 cmp word [terminal_quit],0
 jne .bad
 jmp screen_print_admit
.owner:
 cmp word [_printer_device_result+12],0
 jne .bad
 cmp word [_printer_device_result+10],0
 jne .ok
 call _printer_device_begin
 or ax,ax
 jz .ok
 cmp ax,5
 je .bad
 call terminal_printer_failure
.bad:
 stc
 ret
.ok:
 clc
 ret

; AX byte; pump a bounded poll before every admission. No parser runs here.
screen_print_put:
 push ax
.room:
 call screen_print_service
 jc .failed
 cmp word [terminal_printer_count],128
 jae .room
 pop ax
 push ax
 call terminal_printer_put_raw
 add sp,2
 inc word [terminal_screen_print_bytes]
 clc
 ret
.failed:
 pop ax
 stc
 ret
screen_print_service:
 call terminal_poll_serial
 call terminal_printer_poll
 cmp word [terminal_quit],0
 jne .bad
 cmp word [uart_rx_dropped],0
 je .owner
 mov word [terminal_exit_code],6
 mov word [terminal_quit],1
 jmp .bad
.owner:
 cmp word [_printer_device_result+10],0
 je .bad
 call keyboard_poll
 or ax,ax
 jz .ok
 call terminal_read_key
 cmp ax,0x2d00
 je .quit
 cmp al,27
 je .bad
 call terminal_defer_key
 cmp word [terminal_quit],0
 jne .bad
.ok:
 clc
 ret
.quit:
 mov word [terminal_quit],1
.bad:
 stc
 ret

SEGMENT _DATA public class=DATA use16
global terminal_screen_print_active,terminal_screen_print_action
global terminal_screen_print_bytes
terminal_screen_print_active: dw 0
terminal_screen_print_action: dw 0 ;1printed,2denied,3canceled,4device failure
terminal_screen_print_bytes: dw 0 ;Bytes admitted, not claimed physically printed.
screen_print_mode: dw 0
screen_print_position: dw 0
screen_print_row_end: dw 0
screen_print_temporary: dw 0
screen_print_epoch: dw 0
screen_print_notices: dw screen_print_ok,screen_print_denied
 dw screen_print_canceled,screen_print_error
screen_print_ok: db 'Screen printed',0
screen_print_denied: db 'Print denied',0
screen_print_canceled: db 'Print canceled',0
screen_print_error: db 'Print error',0
