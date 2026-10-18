; Maintained live policy around recovered insert/delete-line helpers.
; NETWORK interprets ANSI CSI M as delete-lines. ORIGINAL preserves the ANSI
; alternate discard-until-Control-N operation with a bounded, serviced wait.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern csi_insert_line,csi_delete_line,screen_set_cursor
extern terminal_ansi_m_policy,ansi_parameters
extern screen_cursor_row,screen_cursor_column,screen_first_row,screen_last_row
extern csi_last_row,screen_cursor_wrap,screen_attribute_checks
extern terminal_poll_io,terminal_tick_low,uart_receive_byte,terminal_quit
extern terminal_abort
extern connection_state
global csi_service_d668,csi_service_d73c,csi_service_daf2

; NETWORK clips repetition to the active region and preserves the column.
; ORIGINAL calls the recovered per-line operation with its original semantics.
csi_service_d668:
 cmp word [terminal_ansi_m_policy],0
 jne .original
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 push word [screen_cursor_column]
 call csi_insert_line
 pop dx
 mov ax,[screen_cursor_row]
 call screen_set_cursor
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
.original:
 jmp csi_insert_line

csi_service_d73c:
 cmp word [terminal_ansi_m_policy],0
 jne .original
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 push word [screen_cursor_column]
 call csi_delete_line
 pop dx
 mov ax,[screen_cursor_row]
 call screen_set_cursor
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
.original:
 jmp csi_delete_line

; CF0 AX=clipped count, CF1 no operation outside a valid scrolling region.
; Mutating the parser count bounds the original dispatcher's repetition too.
line_edit_region:
 cmp word [screen_attribute_checks],0
 jne .outside
 mov ax,[screen_cursor_row]
 cmp ax,[screen_first_row]
 jb .outside
 cmp ax,[screen_last_row]
 ja .outside
 mov dx,[screen_last_row]
 cmp dx,[csi_last_row]
 ja .outside
 cmp word [screen_cursor_wrap],0
 jne .unsupported_attributes
 sub dx,ax
 inc dx
 mov ax,[ansi_parameters]
 cmp ax,1
 jge .positive
 mov ax,1
.positive:
 cmp ax,dx
 jbe .count
 mov ax,dx
.count:
 mov [ansi_parameters],ax
 clc
 ret
.outside:
 mov word [ansi_parameters],1
 stc
 ret
.unsupported_attributes:
 mov ax,0x2d98
 jmp terminal_abort

csi_service_daf2:
 cmp word [terminal_ansi_m_policy],0
 jne terminal_wait_control_n
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 mov si,ax
 push word [screen_cursor_column]
.line:
 call csi_delete_line
 dec si
 jnz .line
 pop dx
 mov ax,[screen_cursor_row]
 call screen_set_cursor
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; The exact original loop is retained in reconstruction/line_edit but is not
; linked here: it neither services flow nor times out. Keep the observable byte
; terminator/local-Escape contract while preserving Alt-X and a36-tick deadline.
global terminal_wait_control_n
terminal_wait_control_n:
 push bp
 push si
 push di
 push es
 mov word [terminal_ansi_wait_active],1
 mov word [terminal_ansi_wait_cancel],0
 mov word [terminal_ansi_wait_timed_out],0
 call terminal_tick_low
 mov si,ax
.poll:
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne .done
 cmp word [terminal_ansi_wait_cancel],0
 jne .done
 cmp word [connection_state],0
 je .receive
 cmp word [connection_state],6
 jne .done ; Return RX ownership to an active modem operation.
.receive:
 call uart_receive_byte
 cmp ax,14
 je .done
 call terminal_tick_low
 sub ax,si
 cmp ax,36
 jb .poll
 mov word [terminal_ansi_wait_timed_out],1
.done:
 mov word [terminal_ansi_wait_active],0
 pop es
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public class=DATA use16
global terminal_ansi_wait_active,terminal_ansi_wait_cancel,terminal_ansi_wait_timed_out
terminal_ansi_wait_active: dw 0
terminal_ansi_wait_cancel: dw 0
terminal_ansi_wait_timed_out: dw 0
