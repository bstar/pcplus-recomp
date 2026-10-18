; Native editor persistence and deferred per-directory connection accounting.
; The only live file writes occur in the startup browser or after UART restore.
BITS 16
CPU 8086
%include "directory_replace.inc"
SEGMENT _TEXT public class=CODE use16
extern terminal_directory_edit,_directory_save_record
extern terminal_directory_path
global terminal_directory_edit_selected
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
; Near C(entry,record114), caller removes4. AX0cancel/1saved/2error/3installed-warning.
terminal_directory_edit_selected:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
 pop es
 cld
 mov si,[bp+6]
 mov di,editor_before
 mov cx,114
 rep movsb
 mov si,editor_before
 mov di,editor_after
 mov cx,114
 rep movsb
 mov ax,editor_after
 push ax
 call terminal_directory_edit
 add sp,2
 or ax,ax
 jz .done
 push ds
 pop es
 cld
 mov di,directory_edit_result
 xor ax,ax
 mov cx,DR_RESULT_SIZE/2
 rep stosw
 mov ax,directory_edit_result
 push ax
 mov ax,editor_after
 push ax
 mov ax,editor_before
 push ax
 push word [bp+4]
 mov ax,terminal_directory_path
 push ax
 call _directory_save_record
 add sp,10
 mov [directory_edit_status],ax
 or ax,ax
 jz .saved
 mov ax,2
 cmp word [directory_edit_result+DR_INSTALLED],0
 je .done
 inc ax
 jmp .done
.saved:
 mov ax,1
.done:
 restore

SEGMENT _DATA public class=DATA use16
global directory_edit_result,directory_edit_status
editor_before: times 114 db 0
editor_after: times 114 db 0
directory_edit_result: times DR_RESULT_SIZE db 0
directory_edit_status: dw 0
