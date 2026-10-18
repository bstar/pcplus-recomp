; Explicit memory CRT/UART/render/keyboard/UI boundaries. No real device/file IO.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern monitor_run_original
%macro MONITOR_OWNER_GUARD 0
 cmp word [monitor_active],1
 jne %%bad
 cmp word [monitor_hook],0
 je %%done
%%bad:
 inc word [fixture_bad_owner_calls]
%%done:
%endmacro
GLOBAL _monitor_dos_test
_monitor_dos_test:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov [fixture_expected_sp],sp
 mov [fixture_expected_bp],bp
 mov ax,ds
 mov [fixture_expected_ds],ax
 mov si,0x1357
 mov di,0x2468
 call monitor_run_original
 cmp word [monitor_active],0
 jne .failed
 cmp word [monitor_hook],0xbeef
 jne .failed
 cmp word [fixture_clear_calls],2
 jne .failed
 cmp word [fixture_render_count],256
 jne .failed
 cmp word [fixture_putc_calls],256
 jne .failed
 cmp word [fixture_file_count],256
 jne .failed
 cmp word [fixture_dispatch_calls],1
 jne .failed
 cmp word [fixture_close_calls],1
 jne .failed
 cmp word [fixture_open_calls],2
 jne .failed
 cmp word [fixture_visible_count],0
 jne .failed
 cmp word [fixture_hook_during_clear],0xbeef
 jne .failed
 cmp si,0x1357
 jne .failed
 cmp di,0x2468
 jne .failed
 cmp bp,[fixture_expected_bp]
 jne .failed
 cmp sp,[fixture_expected_sp]
 jne .failed
 mov ax,ds
 cmp ax,[fixture_expected_ds]
 jne .failed
 mov ax,ss
 cmp ax,[fixture_expected_ds]
 jne .failed
 mov bx,0
.check:
 cmp [fixture_file+bx],bl
 jne .failed
 mov ax,bx
 shl bx,1
 mov dx,[fixture_render_values+bx]
 shr bx,1
 cmp ax,0
 jne .notnul
 mov ax,0x30
.notnul:
 cmp bx,255
 jne .notff
 mov ax,0x3f
.notff:
 cmp ax,dx
 jne .failed
 inc bx
 cmp bx,256
 jb .check
 cmp word [fixture_bad_owner_calls],0
 jne .failed
 cmp word [fixture_guard],0xa55a
 jne .failed
 xor ax,ax
 jmp .return
.failed:
 mov ax,1
.return:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

GLOBAL monitor_status,monitor_clear,monitor_save_window,monitor_restore_window
GLOBAL monitor_draw_text,monitor_open,monitor_close,monitor_putc,monitor_getenv
GLOBAL monitor_dequeue,monitor_render,monitor_keyboard_available,monitor_keyboard_read,monitor_dispatch_key
GLOBAL monitor_prompt_lock,monitor_prompt_unlock,monitor_cursor_position,monitor_cursor_6dca,monitor_cursor_6e5a,monitor_beep
monitor_status:
 inc word [fixture_status_calls]
 ret
monitor_clear:
 inc word [fixture_clear_calls]
 mov word [fixture_visible_count],0
 mov ax,[monitor_hook]
 mov [fixture_hook_during_clear],ax
 ret
monitor_save_window:
 MONITOR_OWNER_GUARD
 inc word [fixture_save_calls]
 mov ax,0x1111
 mov dx,0x7777
 ret
monitor_restore_window:
 MONITOR_OWNER_GUARD
 inc word [fixture_restore_calls]
 ret
monitor_draw_text:
 inc word [fixture_text_calls]
 ret 6
monitor_open:
 push bp
 mov bp,sp
 push bx
 inc word [fixture_open_calls]
 mov ax,[bp+4]
 mov [fixture_last_filename],ax
 mov bx,[bp+6]
 mov [fixture_last_mode],bx
 cmp byte [bx],'r'
 jne .dump
 mov ax,[fixture_probe_result]
 jmp .return
.dump:
 mov ax,[fixture_dump_result]
.return:
 pop bx
 pop bp
 ret
monitor_close:
 push bp
 mov bp,sp
 inc word [fixture_close_calls]
 mov ax,[bp+4]
 mov [fixture_last_close],ax
 or ax,ax
 jnz .valid
 inc word [fixture_null_close_calls]
.valid:
 mov ax,[fixture_close_result]
 pop bp
 ret
monitor_putc:
 MONITOR_OWNER_GUARD
 push bp
 mov bp,sp
 push bx
 inc word [fixture_putc_calls]
 mov ax,[bp+6]
 mov [fixture_last_putc_stream],ax
 or ax,ax
 jnz .valid
 inc word [fixture_null_putc_calls]
 jmp .failed
.valid:
 mov bx,[fixture_file_count]
 cmp bx,[fixture_fail_after]
 jae .failed
 cmp bx,1024
 jae .overflow
 mov ax,[bp+4]
 mov [fixture_file+bx],al
 inc word [fixture_file_count]
 xor ax,ax
 jmp .return
.failed:
 mov ax,0xffff
.return:
 pop bx
 pop bp
 ret
.overflow:
 int3
 jmp .overflow
monitor_getenv:
 inc word [fixture_getenv_calls]
 mov ax,fixture_environment
 cmp word [fixture_env_present],0
 jne .return
 xor ax,ax
.return:
 ret
monitor_dequeue:
 push bx
 mov bx,[fixture_rx_index]
 shl bx,1
 mov ax,[fixture_rx+bx]
 and ax,[fixture_rx_mask]
 inc word [fixture_rx_index]
 dec word [monitor_rx_count]
 pop bx
 ret
monitor_render:
 MONITOR_OWNER_GUARD
 push bp
 mov bp,sp
 push bx
 mov bx,[fixture_render_count]
 cmp bx,512
 jae .overflow
 shl bx,1
 mov ax,[bp+4]
 mov [fixture_render_values+bx],ax
 mov ax,[monitor_active_attribute]
 mov [fixture_render_attributes+bx],ax
 inc word [fixture_render_count]
 inc word [fixture_visible_count]
 pop bx
 pop bp
 ret
.overflow:
 int3
 jmp .overflow
monitor_keyboard_available:
 xor ax,ax
 cmp word [monitor_rx_count],0
 je .ready
 mov ax,[fixture_rx_index]
 cmp ax,[fixture_key_after_rx]
 jb .notyet
.ready:
 mov ax,1
 ret
.notyet:
 xor ax,ax
 ret
monitor_keyboard_read:
 push bx
 mov bx,[fixture_key_index]
 cmp bx,[fixture_key_count]
 jae .empty
 inc word [fixture_key_index]
 shl bx,1
 mov ax,[fixture_keys+bx]
 pop bx
 ret
.empty:
 int3
 jmp .empty
monitor_dispatch_key:
 MONITOR_OWNER_GUARD
 inc word [fixture_dispatch_calls]
 mov ax,[monitor_key]
 mov [fixture_last_dispatch],ax
 ret
monitor_prompt_lock:
 inc word [fixture_lock_calls]
 ret
monitor_prompt_unlock:
 inc word [fixture_unlock_calls]
 ret
monitor_cursor_position:
 inc word [fixture_cursor_calls]
 ret 2
monitor_cursor_6dca:
 inc word [fixture_6dca_calls]
 ret
monitor_cursor_6e5a:
 inc word [fixture_6e5a_calls]
 ret
monitor_beep:
 inc word [fixture_beep_calls]
 ret

SEGMENT _DATA public class=DATA use16
GLOBAL monitor_active,monitor_hook,monitor_prompt_attribute,monitor_choice_attribute
GLOBAL monitor_window_descriptor,monitor_prompt_text,monitor_dump_mode,monitor_dump_name
GLOBAL monitor_help_context,monitor_rx_count,monitor_special_attribute,monitor_active_attribute
GLOBAL monitor_normal_attribute,monitor_key,monitor_environment_name_pointer,monitor_path_before,monitor_path
GLOBAL monitor_probe_mode,monitor_separator,monitor_yes_label,monitor_no_label,monitor_cursor_visibility,monitor_prompt_key
monitor_active dw 0
monitor_hook dw 0xbeef
monitor_prompt_attribute dw 7
monitor_choice_attribute dw 7
monitor_window_descriptor dw 1,5,5,30,monitor_choice_attribute
monitor_prompt_text db 'LOG TO DISK? (Y/N)',0
monitor_dump_mode db 'wb',0
monitor_dump_name db 'PCPLUS.DMP',0
monitor_help_context dw 0
monitor_rx_count dw 256
monitor_special_attribute dw 0x4f
monitor_normal_attribute dw 0x1f
monitor_active_attribute dw 7
monitor_key dw 0
monitor_environment_name_pointer dw fixture_envname
monitor_path_before db 0xa5
monitor_path times 128 db 0
monitor_probe_mode db 'r',0
monitor_separator db '\',0
monitor_yes_label db 'Y',0
monitor_no_label db 'N',0
monitor_cursor_visibility dw 0
monitor_prompt_key dw 0
fixture_envname db 'PCPLUS',0
GLOBAL fixture_rx,fixture_rx_index,fixture_rx_mask,fixture_keys,fixture_key_count,fixture_key_index,fixture_key_after_rx
fixture_rx_index dw 0
fixture_rx_mask dw 255
fixture_rx:
%assign n 0
%rep 256
 dw n
%assign n n+1
%endrep
fixture_keys dw 'Y',0x1c,0x1e61,0x1b
 times 60 dw 0
fixture_key_index dw 0
fixture_key_count dw 4
fixture_key_after_rx dw 0xffff
GLOBAL fixture_probe_result,fixture_dump_result,fixture_env_present,fixture_environment,fixture_close_result,fixture_fail_after
fixture_probe_result dw 0
fixture_dump_result dw 0x2222
fixture_env_present dw 0
fixture_environment db 'D:\LOC',0
 times 64-($-fixture_environment) db 0
fixture_close_result dw 0
fixture_fail_after dw 0xffff
GLOBAL fixture_file,fixture_file_count,fixture_putc_calls,fixture_null_putc_calls,fixture_null_close_calls
fixture_file_count dw 0
fixture_putc_calls dw 0
fixture_null_putc_calls dw 0
fixture_null_close_calls dw 0
fixture_file times 1024 db 0
GLOBAL fixture_guard,fixture_render_values,fixture_render_attributes,fixture_render_count,fixture_visible_count
fixture_guard dw 0xa55a
fixture_render_count dw 0
fixture_visible_count dw 0
fixture_render_values times 512 dw 0
fixture_render_attributes times 512 dw 0
GLOBAL fixture_status_calls,fixture_clear_calls,fixture_save_calls,fixture_restore_calls,fixture_text_calls,fixture_open_calls,fixture_close_calls,fixture_getenv_calls,fixture_dispatch_calls
fixture_status_calls dw 0
fixture_clear_calls dw 0
fixture_save_calls dw 0
fixture_restore_calls dw 0
fixture_text_calls dw 0
fixture_open_calls dw 0
fixture_close_calls dw 0
fixture_getenv_calls dw 0
fixture_dispatch_calls dw 0
GLOBAL fixture_lock_calls,fixture_unlock_calls,fixture_cursor_calls,fixture_6dca_calls,fixture_6e5a_calls,fixture_beep_calls
fixture_lock_calls dw 0
fixture_unlock_calls dw 0
fixture_cursor_calls dw 0
fixture_6dca_calls dw 0
fixture_6e5a_calls dw 0
fixture_beep_calls dw 0
GLOBAL fixture_last_filename,fixture_last_mode,fixture_last_close,fixture_last_putc_stream,fixture_last_dispatch,fixture_hook_during_clear
fixture_last_filename dw 0
fixture_last_mode dw 0
fixture_last_close dw 0
fixture_last_putc_stream dw 0
fixture_last_dispatch dw 0
fixture_hook_during_clear dw 0
fixture_expected_sp dw 0
fixture_expected_bp dw 0
fixture_expected_ds dw 0

GLOBAL fixture_bad_owner_calls
fixture_bad_owner_calls dw 0
