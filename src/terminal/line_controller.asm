; Maintained live policy around recovered insert/delete-line helpers.
; NETWORK interprets ANSI CSI M as delete-lines. ORIGINAL preserves the ANSI
; alternate discard-until-Control-N operation with a bounded, serviced wait.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern line_native_insert_far,line_native_delete_far,attribute_screen_set_cursor_far
extern terminal_ansi_m_policy,ansi_parameters
extern screen_cursor_row,screen_cursor_column,screen_first_row,screen_last_row
extern csi_last_row,screen_cursor_wrap,screen_attribute_checks
extern line_poll_far,line_tick_far,line_receive_far,terminal_quit
extern terminal_ansi_wait_active,terminal_ansi_wait_cancel,terminal_ansi_wait_timed_out
extern repair_abort_far
extern connection_state
extern terminal_line_insert_far,terminal_line_delete_far,attribute_repair_admit_far
global line_insert_controller_far,line_delete_controller_far,line_alternate_controller_far

global line_controller_code_start,line_controller_code_end
line_controller_code_start:

; NETWORK clips repetition to the active region and preserves the column.
; ORIGINAL calls the recovered per-line operation with its original semantics.
line_insert_controller_far:
 cmp word [terminal_ansi_m_policy],0
 jne .original
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 push word [screen_cursor_column]
 call far terminal_line_insert_far
 pop dx
 mov ax,[screen_cursor_row]
 call far attribute_screen_set_cursor_far
.done:
 pop es
 pop di
 pop si
 pop bp
 retf
.original:
 call far line_native_insert_far
 retf

line_delete_controller_far:
 cmp word [terminal_ansi_m_policy],0
 jne .original
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 push word [screen_cursor_column]
 call far terminal_line_delete_far
 pop dx
 mov ax,[screen_cursor_row]
 call far attribute_screen_set_cursor_far
.done:
 pop es
 pop di
 pop si
 pop bp
 retf
.original:
 call far line_native_delete_far
 retf

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
 je .attributes_ready
 push ax
 call far attribute_repair_admit_far
 pop ax
 jc .unsupported_attributes
.attributes_ready:
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
 jmp far repair_abort_far

line_alternate_controller_far:
 cmp word [terminal_ansi_m_policy],0
 jne line_wait_controller_far
 push bp
 push si
 push di
 push es
 call line_edit_region
 jc .done
 mov si,ax
 push word [screen_cursor_column]
.line:
 call far terminal_line_delete_far
 dec si
 jnz .line
 pop dx
 mov ax,[screen_cursor_row]
 call far attribute_screen_set_cursor_far
.done:
 pop es
 pop di
 pop si
 pop bp
 retf

; The exact original loop is retained in reconstruction/line_edit but is not
; linked here: it neither services flow nor times out. Keep the observable byte
; terminator/local-Escape contract while preserving Alt-X and a36-tick deadline.
global line_wait_controller_far
extern terminal_aspect_active,terminal_render_read_now
line_wait_controller_far:
 push bp
 push si
 push di
 push es
 mov word [terminal_ansi_wait_active],1
 mov word [terminal_ansi_wait_cancel],0
 mov word [terminal_ansi_wait_timed_out],0
 call far line_tick_far
 mov si,ax
.poll:
 call far line_poll_far
 cmp word [terminal_quit],0
 jne .done
 cmp word [terminal_ansi_wait_cancel],0
 jne .done
 cmp word [connection_state],0
 je .receive
 cmp word [connection_state],6
 jne .done ; Return RX ownership to an active modem operation.
.receive:
 cmp word [terminal_aspect_active],0
 je .ordinary_receive
 call far terminal_render_read_now
 jmp .received
.ordinary_receive:
 call far line_receive_far
.received:
 cmp ax,14
 je .done
 call far line_tick_far
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
 retf

line_controller_code_end:
