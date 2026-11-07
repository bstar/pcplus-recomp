; Owned DOS test launcher. Record EXEC status before COMMAND.COM consumes it.
BITS 16
CPU 8086
ORG 100h
start:
 cli
 mov ax,cs
 mov ss,ax
 mov sp,stack_top
 sti
 mov ds,ax
 mov es,ax
 mov [parameters+4],ax
 mov [parameters+8],ax
 mov [parameters+12],ax
 mov bx,(stack_top-$$+100h+15)/16
 mov ah,4ah
 int 21h
 jc failed
 mov dx,program
 mov bx,parameters
 mov ax,4b00h
 int 21h
 ; A child may return with arbitrary stack/data registers.
 mov [cs:exec_ax],ax
 mov byte [cs:exec_failed],0
 jnc context
 mov byte [cs:exec_failed],1
context:
 cli
 mov ax,cs
 mov ss,ax
 mov sp,stack_top
 mov ds,ax
 mov es,ax
 sti
 cmp byte [exec_failed],0
 jne failed_exec
 mov ah,4dh
 int 21h
 mov [status+4],ax
 jmp write
failed_exec:
 mov ax,[exec_ax]
failed:
 mov word [status],1
 mov [status+2],ax
 mov word [status+4],0ff7eh
write:
 mov dx,report
 xor cx,cx
 mov ah,3ch
 int 21h
 jc report_failed
 mov bx,ax
 mov dx,status
 mov cx,6
 mov ah,40h
 int 21h
 jc report_failed
 cmp ax,6
 jne report_failed
 mov ah,3eh
 int 21h
 jc report_failed
 mov ax,[status+4]
 mov ah,4ch
 int 21h
report_failed:
 mov ax,4c7fh
 int 21h
parameters: dw 0,80h,0,5ch,0,6ch,0
status: dw 0,0,0ffffh
exec_ax: dw 0
exec_failed: db 0
program: db 'C:\TERMINAL.EXE',0
report: db 'D:\EXITCODE.BIN',0
align 2
times 256 db 0
stack_top:
