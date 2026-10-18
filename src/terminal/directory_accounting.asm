; Native editor persistence and deferred per-directory connection accounting.
; The only live file writes occur in the startup browser or after UART restore.
BITS 16
CPU 8086
%include "directory_live.inc"
%include "directory_replace.inc"
SEGMENT _TEXT public class=CODE use16
extern _directory_save_accounting
extern terminal_directory_path,terminal_directory_entry,terminal_directory_plan
extern terminal_option_mask,terminal_exit_code
global terminal_directory_note_connected
global terminal_directory_flush_accounting
%macro save 0
 push bp
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
 pop bp
 ret
%endmacro
; Capture the DOS calendar and count in RAM only, once per successful connection.
terminal_directory_note_connected:
 push ax
 save
 test word [terminal_option_mask],64
 jz .done
 mov byte [directory_pending],1
 inc word [directory_pending_count]
 mov ah,0x2a
 push ds
 int 0x21
 pop ds
 mov [directory_pending_year],cx
 xor ax,ax
 mov al,dh
 mov [directory_pending_month],ax
 mov al,dl
 mov [directory_pending_day],ax
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 pop ax
 ret

; Called after IRQ/UART/PIC restoration, including exceptional terminal exits.
; Failure returns AX1 and preserves a preexisting application errorlevel.
terminal_directory_flush_accounting:
 save
 cmp byte [directory_pending],0
 je .success
 push ds
 pop es
 cld
 mov di,directory_account_result
 xor ax,ax
 mov cx,DR_RESULT_SIZE/2
 rep stosw
 mov ax,directory_account_result
 push ax
 push word [directory_pending_count]
 push word [directory_pending_day]
 push word [directory_pending_month]
 push word [directory_pending_year]
 mov ax,terminal_directory_plan+DL_RECORD
 push ax
 push word [terminal_directory_entry]
 mov ax,terminal_directory_path
 push ax
 call _directory_save_accounting
 add sp,16
 mov [directory_account_status],ax
 or ax,ax
 jnz .failed
 mov byte [directory_pending],0
 mov word [directory_pending_count],0
.success:
 xor ax,ax
 jmp .done
.failed:
 cmp word [directory_account_result+DR_INSTALLED],0
 je .not_installed
 mov byte [directory_pending],0
 mov word [directory_pending_count],0
.not_installed:
 cmp word [terminal_exit_code],0
 jne .failure_status
 mov word [terminal_exit_code],9
.failure_status:
 mov ax,1
.done:
 restore

SEGMENT _DATA public class=DATA use16
global directory_account_result,directory_account_status,directory_pending_count,directory_pending
directory_account_result: times DR_RESULT_SIZE db 0
directory_account_status: dw 0
directory_pending: db 0
directory_pending_count: dw 0
directory_pending_year: dw 0
directory_pending_month: dw 0
directory_pending_day: dw 0
