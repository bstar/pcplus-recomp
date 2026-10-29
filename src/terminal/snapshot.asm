; Maintained checked screen-file owner around recovered3446/64b8 row helpers.
; Freeze the entire view before DOS IO; UART ISR remains enabled throughout.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern snapshot_row_original
extern _snapshot_file_begin,_snapshot_file_append,_snapshot_file_close
extern _snapshot_file_cleanup,_snapshot_file_result
extern terminal_connection_notice,terminal_connection_notice_restore
extern terminal_poll_serial,terminal_quit,terminal_exit_code,uart_rx_dropped
extern terminal_macro_active,terminal_program_pending,terminal_ansi_wait_active
extern terminal_transfer_pending,terminal_transfer_active,connection_state
extern screen_attribute_row_bytes,screen_video_row_bytes,ui_flow_region_cells
extern text_video_segment,text_cga_status_port,screen_viewport_enabled
extern erase_shadow_offset,erase_shadow_segment,erase_shadow_cells
extern ui_flow_suppressed
extern terminal_monitor_active
extern terminal_controller_active
global terminal_snapshot_start,terminal_snapshot_shutdown
global terminal_snapshot_failed,terminal_snapshot_active,terminal_snapshot_rows_written
global terminal_snapshot_last_action
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
terminal_snapshot_start:
 save
%ifdef TERMINAL_DIRECTORY_STORAGE
 extern _redisplay_active,_command_menu_active
 mov ax,[_redisplay_active]
 or ax,[_command_menu_active]
 jnz .denied
%endif
 cmp word [terminal_controller_active],0
 jne .denied
 cmp word [terminal_monitor_active],0
 jne .denied
 cmp word [terminal_snapshot_active],0
 jne .denied
 cmp word [terminal_macro_active],0
 jne .denied
 cmp word [terminal_program_pending],0
 jne .denied
%ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 extern terminal_program_active
 cmp word [terminal_program_active],0
 jne .denied
%endif
 cmp word [terminal_ansi_wait_active],0
 jne .denied
 cmp word [terminal_transfer_pending],0
 jne .denied
 cmp word [terminal_transfer_active],0
 jne .denied
 cmp word [connection_state],0
 je .geometry
 cmp word [connection_state],6
 jne .denied
.geometry:
 ; The live renderer supports this geometry. Other original modes remain in
 ; the native diagnostic; never read an unvalidated far screen in the app.
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .denied
 cmp ah,80
 jne .denied
 or bh,bh
 jnz .denied
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x84],0 ;Legacy BIOS without EGA row-count byte: mode3 is25.
 je .rows_ready
 cmp byte [es:0x84],24
 jne .denied
.rows_ready:
 cmp word [screen_attribute_row_bytes],80
 jne .denied
 cmp word [screen_video_row_bytes],160
 jne .denied
 cmp word [ui_flow_region_cells],80
 jne .denied
 cmp word [text_video_segment],0xb800
 jne .denied
 cmp word [text_cga_status_port],0
 jne .denied ; Native retrace wait is unbounded; do not enter it live.
 cmp word [screen_viewport_enabled],0
 je .freeze
 mov ax,seg erase_shadow_cells
 cmp ax,[erase_shadow_segment]
 jne .denied
 cmp word [erase_shadow_offset],erase_shadow_cells
 jne .denied
.freeze:
 call terminal_connection_notice_restore
 mov word [terminal_snapshot_rows_written],0
 mov word [snapshot_row_index],0
 mov word [snapshot_status_row],25
 cmp word [ui_flow_suppressed],0
 jne .read_row
 mov word [snapshot_status_row],24
.read_row:
 mov ax,snapshot_row_buffer
 push ax
 push word [snapshot_row_index]
 call snapshot_row_original
 add sp,4
 cmp ax,80
 ja .denied
 mov bx,[snapshot_row_index]
 mov [snapshot_row_lengths+bx],al
 mov ax,80
 mul bx
 mov di,ax
 add di,terminal_snapshot_image
 mov es,[terminal_snapshot_image_segment]
 mov si,snapshot_row_buffer
 mov cx,80
 cld
 rep movsb
 inc word [snapshot_row_index]
 cmp word [snapshot_row_index],25
 jb .read_row
 ; No DOS/foreground service ran during freezing. Only the UART ISR can have
 ; changed RX state; all file writes now read this immutable private image.
 mov ax,2 ;CF_APPEND
 push ax
 mov ax,snapshot_path
 push ax
 call _snapshot_file_begin
 add sp,4
 cmp ax,4 ;CF_INSPECT
 jne .begun
 cmp word [_snapshot_file_result+4],2 ;Actual DOS file-not-found only
 jne .begin_failed
 mov ax,1 ;CF_NEW, exclusive
 push ax
 mov ax,snapshot_path
 push ax
 call _snapshot_file_begin
 add sp,4
.begun:
 or ax,ax
 jnz .begin_failed
 mov word [terminal_snapshot_active],1
 mov word [snapshot_row_index],0
.write_row:
 call terminal_poll_serial
 cmp word [uart_rx_dropped],0
 jne .overflow
 cmp word [terminal_quit],0
 jne .canceled
 mov bx,[snapshot_row_index]
 mov ax,80
 mul bx
 mov si,ax
 add si,terminal_snapshot_image
 push ds
 mov ax,ds
 mov es,ax
 mov ax,[terminal_snapshot_image_segment]
 mov ds,ax
 mov di,snapshot_row_buffer
 mov cx,80
 cld
 rep movsb
 pop ds
 mov bx,[snapshot_row_index]
 xor ax,ax
 mov al,[snapshot_row_lengths+bx]
 mov di,ax
 ; Native3496 replaces a final1Ah on the status row with a space after
 ; appending CRLF. Guard empty rows instead of its unchecked buffer[-1].
 cmp bx,[snapshot_status_row]
 jne .newline
 or di,di
 jz .newline
 cmp byte [snapshot_row_buffer+di-1],0x1a
 jne .newline
 mov byte [snapshot_row_buffer+di-1],32
.newline:
 mov byte [snapshot_row_buffer+di],13
 mov byte [snapshot_row_buffer+di+1],10
 add ax,2
 push ax
 mov ax,snapshot_row_buffer
 push ax
 call _snapshot_file_append
 add sp,4
 or ax,ax
 jnz .write_failed
 inc word [terminal_snapshot_rows_written]
 inc word [snapshot_row_index]
 cmp word [snapshot_row_index],25
 jb .write_row
 call _snapshot_file_close
 or ax,ax
 jnz .close_failed
 mov word [terminal_snapshot_active],0
 mov word [terminal_snapshot_last_action],1
 mov si,snapshot_saved
 jmp .notice
.overflow:
 mov word [terminal_exit_code],6
 mov word [terminal_quit],1
.canceled:
 mov ax,3 ;CF_STATE; snapshot may contain a checked prefix of complete rows.
.write_failed:
 call snapshot_remember_failure
 call _snapshot_file_close
.close_failed:
 or ax,ax
 jz .failed_notice
 call snapshot_remember_failure
.failed_notice:
 mov word [terminal_snapshot_active],0
 mov word [terminal_snapshot_last_action],3
 mov si,snapshot_error
 jmp .notice
.begin_failed:
 cmp word [_snapshot_file_result+12],0 ;Ambiguous close after failed seek
 je .denied
 call snapshot_remember_failure
 mov word [terminal_snapshot_last_action],3
 mov si,snapshot_error
 jmp .notice
.denied:
 mov word [terminal_snapshot_last_action],2
 mov si,snapshot_denied
.notice:
 ; The native notice renderer also waits for CGA retrace. An unsupported CGA
 ; request must return without entering that wait merely to draw its denial.
 cmp word [text_cga_status_port],0
 jne .restore
 call terminal_connection_notice
.restore:
 restore
snapshot_remember_failure:
 cmp word [terminal_snapshot_failed],0
 jne .done
 mov [terminal_snapshot_failed],ax
.done:
 ret
; AX=first genuine snapshot failure or0. Do not turn a rejected open without
; an acquired handle into a shutdown error; never retry an ambiguous close.
terminal_snapshot_shutdown:
 push bp
 push si
 push di
 push es
 cmp word [_snapshot_file_result+10],0
 jne .cleanup
 cmp word [_snapshot_file_result+12],0
 je .status
.cleanup:
 call _snapshot_file_cleanup
 or ax,ax
 jz .status
 call snapshot_remember_failure
.status:
 mov ax,[terminal_snapshot_failed]
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
terminal_snapshot_failed: dw 0
terminal_snapshot_last_action: dw 0 ;0 untouched,1 saved,2 denied,3 failed
terminal_snapshot_active: dw 0
terminal_snapshot_rows_written: dw 0
snapshot_row_index: dw 0
snapshot_status_row: dw 24
snapshot_row_lengths: times 25 db 0
snapshot_row_buffer: times 82 db 0
snapshot_path: db 'PCPLUS.SCR',0
snapshot_saved: db 'Screen saved',0
snapshot_denied: db 'Screen denied',0
snapshot_error: db 'Screen error',0
global terminal_snapshot_image_segment
terminal_snapshot_image_segment: dw seg terminal_snapshot_image
%ifdef TERMINAL_DIRECTORY_STORAGE
extern terminal_snapshot_image,terminal_snapshot_image_end
%else
SEGMENT SNAPSHOT_STORAGE public align=16 class=FAR_DATA use16
global terminal_snapshot_image,terminal_snapshot_image_end
terminal_snapshot_image: resb 2000
terminal_snapshot_image_end:
%endif
