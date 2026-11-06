; Foreground PROGRAM-kind11 binding for the exact resident57AE producer.
; Owns no new DGROUP bytes. The52-byte queued command is exclusively borrowed
; while kind11 runs; the resolver's two64-byte outputs remain on this stack.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
global _terminal_help_execute,help_resolve,help_format_tail,help_execute
extern context_help_native,_resource_program_path,process_run_far,process_psp
extern terminal_program_command,attributes_normal_value,attributes_bold_value,attributes_reverse_value
extern mouse_scale_x,mouse_scale_y
help_path_key equ terminal_program_command
help_title equ terminal_program_command+11
help_tail_format equ terminal_program_command+24
help_program_key equ terminal_program_command+36
help_ui_1d3e equ terminal_program_command+48
help_topic equ terminal_program_command+50
help_normal equ attributes_normal_value
help_bold equ attributes_bold_value
help_reverse equ attributes_reverse_value
help_mouse_x equ mouse_scale_x
help_mouse_y equ mouse_scale_y
help_path: dw 0
help_exe: dw 0
help_result: dw 0
template: db 'PCPLUS.HLP',0,'PROCOMM PLUS',0,' PCHELP %lu',0,'PCHELP.RTE',0,0
; FAR C(result*). Both bounded sibling paths must resolve before the native
; unbounded strcpy is permitted to execute.64 bytes fit its66-byte path slot.
_terminal_help_execute:
 push bp
 mov bp,sp
 sub sp,128
 push si
 push di
 push es
 mov ax,4
 cmp word [cs:help_result],0
 jne .done
 mov ax,[bp+6]
 or ax,ax
 jz .invalid
 mov [cs:help_result],ax
 push ds
 pop es
 push ds
 push cs
 pop ds
 mov si,template
 mov di,help_path_key
 mov cx,48
 cld
 rep movsb
 pop ds
 mov word [help_ui_1d3e],0 ; Unresolved native UI word: explicit maintained default.
 lea ax,[bp-64]
 mov [cs:help_path],ax
 push ax
 mov ax,help_path_key
 push ax
 push word [process_psp]
 call _resource_program_path
 add sp,6
 or ax,ax
 jnz .path_failed
 lea ax,[bp-128]
 mov [cs:help_exe],ax
 push ax
 mov ax,help_program_key
 push ax
 push word [process_psp]
 call _resource_program_path
 add sp,6
 or ax,ax
 jnz .path_failed
 call context_help_native
 jmp .release
.path_failed:
 mov ax,1
.release:
 mov word [cs:help_path],0
 mov word [cs:help_exe],0
 mov word [cs:help_result],0
 jmp .done
.invalid:
 mov ax,1
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
help_resolve:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 cmp ax,help_path_key
 mov ax,[cs:help_path]
 je .done
 mov ax,[cs:help_exe]
.done:
 pop bp
 ret
; Fixed native sprintf ABI: (output,format,low,high). Only the known prefix
; and unsigned decimal pointer are formatted; no CRT/near-bank import.
help_format_tail:
 push bp
 mov bp,sp
 sub sp,12
 push si
 push di
 mov di,[bp+4]
 mov si,[bp+6]
 mov cx,8
 cld
.prefix:
 lodsb
 mov [di],al
 inc di
 loop .prefix
 mov ax,[bp+8]
 mov cx,[bp+10]
 mov bx,10
 lea si,[bp-1]
 mov byte [si],0
.digit:
 push ax
 mov ax,cx
 xor dx,dx
 div bx
 mov cx,ax
 pop ax
 div bx
 add dl,'0'
 dec si
 mov [si],dl
 mov dx,ax
 or dx,cx
 jnz .digit
.copy:
 lodsb
 mov [di],al
 inc di
 or al,al
 jnz .copy
 mov ax,di
 sub ax,[bp+4]
 dec ax
 pop di
 pop si
 mov sp,bp
 pop bp
 ret
help_execute:
 push bp
 mov bp,sp
 push word [cs:help_result]
 push word [bp+6]
 push word [bp+4]
 call far process_run_far
 add sp,6
 or ax,ax
 jnz .done
 mov bx,[cs:help_result]
 cmp word [bx+4],0
 je .done
 mov ax,1 ; A source helper's nonzero exit is an application failure.
.done:
 pop bp
 ret
