; Maintained foreground raw monitor. Actual UART bytes bypass ANSI/log/history;
; native0730 renders literal cells using the recovered three special-byte rules.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _monitor_file_begin,_monitor_file_append,_monitor_file_close
extern _monitor_file_cleanup,_monitor_file_result
extern terminal_clear_home,render_character,attributes_current
extern attributes_normal_value,attributes_bold_value
extern terminal_connection_notice,terminal_connection_notice_restore
extern terminal_clock_ticks,terminal_quit,terminal_exit_code,uart_rx_dropped
extern terminal_macro_active,terminal_program_pending,terminal_program_active
extern terminal_ansi_wait_active,terminal_parser_active
extern terminal_transfer_pending,terminal_transfer_active,terminal_snapshot_active
extern connection_state,text_cga_status_port,text_video_segment
extern screen_viewport_enabled,screen_attribute_row_bytes,screen_video_row_bytes
extern ui_flow_region_cells,keyboard_classify_raw,terminal_enqueue_key_slot,terminal_enqueue_al
global terminal_monitor_start,terminal_monitor_key,terminal_monitor_filter
GLOBAL terminal_monitor_poll,terminal_monitor_stop,terminal_monitor_shutdown
GLOBAL terminal_monitor_active,terminal_monitor_logging,terminal_monitor_failed
GLOBAL terminal_monitor_last_action,terminal_monitor_buffer_count
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
terminal_monitor_start:
 save
 cmp word [terminal_monitor_active],0
 jne .done
 cmp word [terminal_parser_active],0
 jne .denied
 cmp word [terminal_macro_active],0
 jne .denied
 cmp word [terminal_program_pending],0
 jne .denied
 cmp word [terminal_program_active],0
 jne .denied
 cmp word [terminal_ansi_wait_active],0
 jne .denied
 cmp word [terminal_transfer_pending],0
 jne .denied
 cmp word [terminal_transfer_active],0
 jne .denied
 cmp word [terminal_snapshot_active],0
 jne .denied
 cmp word [_monitor_file_result+10],0
 jne .denied
 cmp word [_monitor_file_result+12],0
 jne .denied
 cmp word [connection_state],0
 je .geometry
 cmp word [connection_state],6
 jne .denied
.geometry:
 ; Do not enter native unbounded CGA waits or unsupported far/view geometry.
 cmp word [text_cga_status_port],0
 jne .denied
 cmp word [text_video_segment],0xb800
 jne .denied
 cmp word [screen_attribute_row_bytes],80
 jne .denied
 cmp word [screen_video_row_bytes],160
 jne .denied
 cmp word [ui_flow_region_cells],80
 jne .denied
 cmp word [screen_viewport_enabled],0
 jne .denied
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
 cmp byte [es:0x84],0
 je .begin
 cmp byte [es:0x84],24
 jne .denied
.begin:
 call terminal_connection_notice_restore
 call terminal_clear_home
 mov word [terminal_monitor_active],2
 mov word [terminal_monitor_logging],0
 mov word [terminal_monitor_buffer_count],0
 mov word [monitor_connected],0
 cmp word [connection_state],6
 jne .prompt
 mov word [monitor_connected],1
.prompt:
 mov word [terminal_monitor_last_action],1
 mov ax,0xb800
 mov es,ax
 mov di,3840
 mov ax,0x1f20
 mov cx,80
 cld
 rep stosw
 mov di,3840
 mov si,monitor_prompt
.prompt_char:
 lodsb
 or al,al
 jz .done
 mov ah,0x1f
 stosw
 jmp .prompt_char
.denied:
 mov word [terminal_monitor_last_action],2
.done:
 restore

; AX raw BIOS key, CF1 consumed, CF0 normal handling. Preserve raw AX.
; Monitor owns RX and suppresses nested local/KEY/TEXT/PROGRAM entry. Ordinary
; literal keys and configured network binding slots still use the real TX queue.
terminal_monitor_key:
 save
 cmp word [terminal_monitor_active],0
 jne .owned
 cmp al,0x1c
 jne .not_mine
 call terminal_monitor_start
 jmp .consumed
.owned:
 cmp ax,0x2d00
 je .leave_normal
 cmp ax,0x2300
 je .leave_normal
 cmp al,0x1c
 je .consumed
 cmp word [terminal_monitor_active],2
 jne .view_key
 cmp al,'y'
 je .log
 cmp al,'Y'
 je .log
 cmp al,'n'
 je .view
 cmp al,'N'
 je .view
 cmp al,13
 je .view
 cmp al,27
 jne .consumed
.view:
 call terminal_connection_notice_restore
 call terminal_clear_home
 mov word [terminal_monitor_active],1
 jmp .consumed
.log:
 mov ax,3 ;CF_REPLACE is admitted only by this owner, after explicit Y.
 push ax
 mov ax,monitor_path
 push ax
 call _monitor_file_begin
 add sp,4
 or ax,ax
 jnz .open_failed
 mov word [terminal_monitor_logging],1
 jmp .view
.open_failed:
 cmp word [_monitor_file_result+10],0
 jne .acquired_failure
 cmp word [_monitor_file_result+12],0
 je .view_denied
.acquired_failure:
 call monitor_failure
.view_denied:
 call terminal_clear_home
 mov word [terminal_monitor_active],1
 mov word [terminal_monitor_last_action],3
 mov si,monitor_denied
 call terminal_connection_notice
 jmp .consumed
.view_key:
 cmp al,27
 je .leave
 call keyboard_classify_raw
 cmp ax,79
 jb .binding
 cmp ah,1
 jne .consumed
 call terminal_enqueue_al
 jmp .consumed
.binding:
 call terminal_enqueue_key_slot
 jmp .consumed
.leave:
 call terminal_monitor_stop
 jmp .consumed
.leave_normal:
 call terminal_monitor_stop
.not_mine:
 clc
 restore
.consumed:
 stc
 restore

; AX actual dequeued byte. CF1 consumed or CF0 original AX for normal input.
; File bytes remain exact including NUL/ESC/FF/SUB/CR/LF/DEL; no timestamp/EOF.
terminal_monitor_filter:
 save
 cmp word [terminal_monitor_active],1
 jne .normal
 and ax,0xff
 mov si,ax
 call terminal_connection_notice_restore
 cmp word [terminal_monitor_logging],0
 je .display
 mov bx,[terminal_monitor_buffer_count]
 mov [monitor_buffer+bx],al
 inc bx
 mov [terminal_monitor_buffer_count],bx
 cmp bx,1
 jne .full
 call terminal_clock_ticks
 mov [monitor_last_tick],ax
 mov [monitor_last_tick+2],dx
.full:
 cmp word [terminal_monitor_buffer_count],256
 jb .display
 call monitor_flush
.display:
 mov ax,[attributes_normal_value]
 mov [attributes_current],ax
 mov ax,si
 or ax,ax
 jz .nul
 cmp ax,255
 je .ff
 cmp ax,27
 jne .render
 jmp .special
.nul:
 mov ax,'0'
 jmp .special
.ff:
 mov ax,'?'
.special:
 mov dx,[attributes_bold_value]
 mov [attributes_current],dx
.render:
 push ax
 call render_character
 add sp,2
 stc
 restore
.normal:
 clc
 restore

terminal_monitor_poll:
 save
 cmp word [terminal_monitor_active],0
 je .done
 cmp word [terminal_quit],0
 jne .stop
 cmp word [monitor_connected],0
 je .timer
 cmp word [connection_state],6
 jne .stop
.timer:
 cmp word [terminal_monitor_logging],0
 je .done
 cmp word [terminal_monitor_buffer_count],0
 je .done
 call terminal_clock_ticks
 sub ax,[monitor_last_tick]
 sbb dx,[monitor_last_tick+2]
 jnc .elapsed
 add ax,0x00b0 ;BIOS midnight: day18_00B0 ticks, not a16-bit wrap.
 adc dx,0x0018
.elapsed:
 or dx,dx
 jnz .flush
 cmp ax,18
 jb .done
.flush:
 call monitor_flush
 jmp .done
.stop:
 call terminal_monitor_stop
.done:
 restore

monitor_flush:
 cmp word [terminal_monitor_logging],0
 je .done
 mov ax,[terminal_monitor_buffer_count]
 or ax,ax
 jz .done
 push ax
 mov ax,monitor_buffer
 push ax
 call _monitor_file_append
 add sp,4
 mov word [terminal_monitor_buffer_count],0
 or ax,ax
 jz .done
 call monitor_failure
.done:
 ret
monitor_failure:
 cmp word [terminal_monitor_failed],0
 jne .close
 mov [terminal_monitor_failed],ax
.close:
 mov word [terminal_monitor_logging],0
 mov word [terminal_monitor_last_action],4
 cmp word [_monitor_file_result+10],0
 je .done
 call _monitor_file_close
.done:
 ret

; Resolve only a handle actually acquired. Admission failures are nonfatal;
; ambiguous physical close is never retried. Preserve the first sticky error.
monitor_close:
 call monitor_flush
 mov word [terminal_monitor_logging],0
 cmp word [_monitor_file_result+10],0
 je .done
 call _monitor_file_close
 or ax,ax
 jz .done
 call monitor_failure
.done:
 ret
terminal_monitor_stop:
 save
 cmp word [terminal_monitor_active],0
 je .done
 mov word [terminal_monitor_active],0
 call monitor_close
 call terminal_connection_notice_restore
 call terminal_clear_home
 mov word [terminal_monitor_last_action],5
.done:
 restore
terminal_monitor_shutdown:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov word [terminal_monitor_active],0
 call monitor_close
 mov ax,[terminal_monitor_failed]
 cmp word [_monitor_file_result+12],0
 je .done
 or ax,ax
 jnz .done
 mov ax,11 ;CF_RECOVERY; cleanup cannot safely retry a physical close.
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
terminal_monitor_active: dw 0
terminal_monitor_logging: dw 0
terminal_monitor_failed: dw 0
terminal_monitor_last_action: dw 0
terminal_monitor_buffer_count: dw 0
monitor_connected: dw 0
monitor_last_tick: dd 0
monitor_buffer: times 256 db 0
monitor_path: db 'PCPLUS.DMP',0
monitor_prompt: db ' LOG TO DISK? Y replaces PCPLUS.DMP; N/Enter/Esc: view only',0
monitor_denied: db 'Dump denied',0
