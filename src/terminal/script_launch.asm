; Maintained Script menu -> existing drained PROGRAM owner -> direct ASPECT.
; The child is a standalone interpreter; it does not own terminal serial APIs.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_kind,process_psp
extern terminal_translation_edit_executable,terminal_translation_edit_tail
extern _command_menu_script,_terminal_script_prepare
extern terminal_program_command
global terminal_script_start,terminal_script_prepare
terminal_script_start:
 push si
 push di
 push es
 push ds
 pop es
 cld
 ; PROGRAM validates/copies this stored marker; never invokes it via COMSPEC
 ; because kind4 is installed before the foreground safe point can run.
 mov ax,script_marker
 call terminal_program_start
 or ax,ax
 jnz .done
 mov si,_command_menu_script
 mov di,terminal_translation_edit_tail
 mov al,' '
 stosb
 mov cx,64
.copy:
 lodsb
 stosb
 or al,al
 jz .queued
 loop .copy
 ; Menu guarantees a terminator; defense against an external synthetic action.
 mov byte [terminal_translation_edit_tail+64],0
.queued:
 mov word [terminal_program_kind],4
.done:
 pop es
 pop di
 pop si
 ret
terminal_script_prepare:
 mov ax,terminal_translation_edit_tail
 push ax
 mov ax,terminal_translation_edit_executable
 push ax
 push word [process_psp]
 call _terminal_script_prepare
 add sp,6
 ret
SEGMENT _DATA public class=DATA use16
script_marker: db 'ASPECT',0
