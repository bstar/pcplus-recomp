; Maintained nonblocking KEY/TEXT execution over recovered expansion and UART.
; No shell/script/HOOK execution is substituted for those unfinished services.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_break_hold
extern terminal_option_mask,terminal_actions_path,_key_actions_dos_read
extern modem_expand_bounded,terminal_clock_ticks,uart_try_write
extern terminal_quit,terminal_exit_code,connection_state
extern terminal_program_start,terminal_program_pending,terminal_program_active
extern terminal_monitor_active
extern terminal_controller_active
global terminal_load_actions,terminal_macro_start,terminal_macro_poll
global terminal_macro_cancel,terminal_defer_key,terminal_take_deferred_key

terminal_load_actions:
 push bp
 push si
 push di
 push es
 push ds
 pop es
 cld
 mov di,terminal_action_definitions
 mov cx,10
.default:
 mov ax,3
 stosw
 push cx
 xor ax,ax
 mov cx,52
 rep stosb
 pop cx
 loop .default
 test word [terminal_option_mask],4096
 jz .success
 mov ax,terminal_actions_io
 push ax
 mov ax,terminal_action_definitions
 push ax
 mov ax,terminal_actions_path
 push ax
 call _key_actions_dos_read
 add sp,6
 mov [terminal_actions_status],ax
 or ax,ax
 jz .success
 mov ax,10
 jmp .done
.success:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; AX zero-based Alt1..Alt0 index. AX0 started/empty,1 bad index,
; 2 unsupported action kind,3 unsafe TEXT expansion,4 already busy.
; Preserve BP/SI/DI/ES; BX/CX/DX volatile. No wire byte before validation.
terminal_macro_start:
 push bp
 push si
 push di
 push es
 cmp word [uart_break_hold],0
 jne .busy
 cmp word [terminal_controller_active],0
 jne .busy
 cmp word [terminal_monitor_active],0
 jne .busy
 cmp word [terminal_macro_active],0
 jne .busy
 cmp word [terminal_program_pending],0
 jne .busy
 cmp word [terminal_program_active],0
 jne .busy
 cmp ax,10
 jae .bad_index
 mov bx,54
 mul bx
 mov si,terminal_action_definitions
 add si,ax
 cmp word [si],1
 je .program
 cmp word [si],3
 jne .unsupported
 cmp byte [si+2],0
 je .success
 add si,2
 mov ax,52
 push ax
 push ax
 mov ax,macro_payload
 push ax
 push si
 call modem_expand_bounded
 pushf
 pop dx
 add sp,8
 test dx,1
 jnz .bad_text
 call macro_now
 call macro_progress
 mov ax,[terminal_macro_tx_epoch]
 mov [macro_last_tx_epoch],ax
 mov word [macro_cursor],macro_payload
 mov word [macro_paused],0
 mov word [terminal_macro_active],1
 mov word [terminal_macro_status],1
 jmp .success
.program:
 add si,2
 mov ax,si
 call terminal_program_start
 or ax,ax
 jz .success
 cmp ax,2
 je .busy
 jmp .bad_text
.success:
 xor ax,ax
 jmp .done
.bad_index:
 mov word [terminal_macro_status],5
 mov ax,1
 jmp .done
.unsupported:
 mov word [terminal_macro_status],4
 mov ax,2
 jmp .done
.bad_text:
 mov word [terminal_macro_status],5
 mov ax,3
 jmp .done
.busy:
 mov ax,4
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Called each foreground poll. Ordinary queued output has priority; the caller
; grants at most one physical write with terminal_macro_tx_allowed=1.
; Full-day ticks handle low-word wrap and BIOS midnight, with36 ticks of no
; transmitter progress allowed. Encoded pause is ten ticks, before FF->NUL.
terminal_macro_poll:
 push bp
 push si
 push di
 push es
 cmp word [terminal_macro_active],0
 je .done
 cmp word [terminal_quit],0
 jne .cancel
 cmp word [connection_state],0
 je .clock
 cmp word [connection_state],6
 jne .cancel
.clock:
 call macro_now
 mov ax,[terminal_macro_tx_epoch]
 cmp ax,[macro_last_tx_epoch]
 je .pause
 mov [macro_last_tx_epoch],ax
 call macro_progress
.pause:
 cmp word [macro_paused],0
 je .deadline
 mov bx,macro_pause_tick
 call macro_elapsed
 or dx,dx
 jnz .pause_done
 cmp ax,10
 jb .done
.pause_done:
 mov word [macro_paused],0
 call macro_progress
.deadline:
 mov bx,macro_progress_tick
 call macro_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jae .timeout
 cmp word [terminal_macro_tx_allowed],0
 je .done
 mov si,[macro_cursor]
 lodsb
 or al,al
 jz .finished
 cmp al,[terminal_macro_pause_character]
 je .start_pause
 cmp al,0xff
 jne .write
 xor al,al
.write:
 call uart_try_write
 jc .done
 inc word [terminal_macro_tx_epoch]
 mov ax,[terminal_macro_tx_epoch]
 mov [macro_last_tx_epoch],ax
 mov [macro_cursor],si
 call macro_progress
 jmp .done
.start_pause:
 mov [macro_cursor],si
 mov word [macro_paused],1
 mov ax,[macro_now_tick]
 mov [macro_pause_tick],ax
 mov ax,[macro_now_tick+2]
 mov [macro_pause_tick+2],ax
 jmp .done
.finished:
 mov word [terminal_macro_active],0
 mov word [terminal_macro_status],2
 jmp .done
.timeout:
 call terminal_macro_cancel
 mov word [terminal_macro_status],6
 mov word [terminal_exit_code],10
 mov word [terminal_quit],1
 jmp .done
.cancel:
 call terminal_macro_cancel
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

macro_now:
 call terminal_clock_ticks
 mov [macro_now_tick],ax
 mov [macro_now_tick+2],dx
 ret
macro_progress:
 mov ax,[macro_now_tick]
 mov [macro_progress_tick],ax
 mov ax,[macro_now_tick+2]
 mov [macro_progress_tick+2],ax
 ret
macro_elapsed:
 mov ax,[macro_now_tick]
 mov dx,[macro_now_tick+2]
 sub ax,[bx]
 sbb dx,[bx+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done:
 ret

; Connection/cancel hooks preserve AX and all other registers. Already-written
; bytes cannot be withdrawn; no unsent macro byte is stored in the shared ring.
terminal_macro_cancel:
 cmp word [terminal_macro_active],0
 jne .cancel
 cmp word [macro_pending_count],0
 je .clear
.cancel:
 mov word [terminal_macro_status],3
.clear:
 mov word [terminal_macro_active],0
 mov word [macro_paused],0
 mov word [macro_pending_count],0
 mov word [macro_pending_head],0
 mov word [macro_pending_tail],0
 ret

; Buffer normal keys while TEXT is active, preserving order without blocking
; Escape/Alt-X/Alt-H. AX key; full32-word queue stops explicitly, never drops.
terminal_defer_key:
 push bx
 cmp word [macro_pending_count],32
 jae .full
 mov bx,[macro_pending_tail]
 shl bx,1
 mov [macro_pending_keys+bx],ax
 inc word [macro_pending_tail]
 and word [macro_pending_tail],31
 inc word [macro_pending_count]
 pop bx
 ret
.full:
 call terminal_macro_cancel
 mov word [terminal_macro_status],7
 mov word [terminal_exit_code],3
 mov word [terminal_quit],1
 pop bx
 ret
terminal_take_deferred_key:
 push bx
 cmp word [macro_pending_count],0
 je .empty
 mov bx,[macro_pending_head]
 shl bx,1
 mov ax,[macro_pending_keys+bx]
 inc word [macro_pending_head]
 and word [macro_pending_head],31
 dec word [macro_pending_count]
 pop bx
 clc
 ret
.empty:
 pop bx
 stc
 ret

; A quiesced local prompt must honor keys already retained while its output
; drained. CF distinguishes an empty FIFO from every valid BIOS word, even0.
global terminal_read_foreground_key
terminal_read_foreground_key:
 call terminal_take_deferred_key
 jnc .done
 xor ax,ax
 int 0x16
.done:
 ret

SEGMENT _DATA public class=DATA use16
; Shared bounded foreground typeahead. A pending menu owns these same queued
; keys until its parser-safe opening; aliases expose storage, not new callbacks.
global terminal_deferred_count,terminal_deferred_head,terminal_deferred_tail
terminal_deferred_count equ macro_pending_count
terminal_deferred_head equ macro_pending_head
terminal_deferred_tail equ macro_pending_tail
global terminal_action_definitions,terminal_actions_status,terminal_actions_io
global terminal_macro_active,terminal_macro_status,terminal_macro_pause_character
global terminal_macro_character_delay_units,terminal_macro_tx_allowed,terminal_macro_tx_epoch
terminal_action_definitions:
%rep 10
 dw 3
 times 52 db 0
%endrep
terminal_actions_status: dw 0
terminal_actions_io: times 8 db 0
terminal_macro_active: dw 0
terminal_macro_status: dw 0
terminal_macro_pause_character: db '~'
; Retained original calibrated units; live ordinary TEXT bytes use fast pacing.
terminal_macro_character_delay_units: dw 0
terminal_macro_tx_allowed: dw 0
terminal_macro_tx_epoch: dw 0
macro_payload: times 52 db 0
macro_cursor: dw 0
macro_paused: dw 0
macro_last_tx_epoch: dw 0
macro_now_tick: dd 0
macro_progress_tick: dd 0
macro_pause_tick: dd 0
macro_pending_count: dw 0
macro_pending_head: dw 0
macro_pending_tail: dw 0
macro_pending_keys: times 32 dw 0
