; Test-only startup invocation, before UART/foreground ownership. No hotkey.
; Report8-byte process_result +68-byte current path +2-byte query status.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
extern _gateway_lookup_run,_path_session_current,terminal_program_result
global terminal_gateway_probe
terminal_gateway_probe:
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov di,terminal_program_result
 push ds
 pop es
 xor ax,ax
 mov cx,4
 cld
 rep stosw
 mov ax,terminal_program_result
 push ax
 call far _gateway_lookup_run
 add sp,2
 mov [terminal_program_result],ax
 sub sp,70
 push ds
 pop es
 mov di,sp
 xor ax,ax
 mov cx,35
 rep stosw
 mov di,sp
 push di
 call far _path_session_current
 add sp,2
 mov [di+68],ax
 push ds
 push cs
 pop ds
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 pop ds
 jc .failed
 mov bx,ax
 mov dx,terminal_program_result
 mov cx,8
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,8
 jne .close_failed
 mov dx,di
 mov cx,70
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,70
 jne .close_failed
 mov ah,3eh
 int 21h
 jc .failed
 xor ax,ax
 jmp .done
.close_failed:
 mov ah,3eh
 int 21h
.failed:
 mov ax,1
.done:
 add sp,70
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 retf
name: db 'D:\GWRESULT.BIN',0
