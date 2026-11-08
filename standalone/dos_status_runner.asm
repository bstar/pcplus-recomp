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
%ifdef STATUS_RUNNER_HIGH
 call high_prepare
 jc failed
%endif
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
%ifdef STATUS_RUNNER_HIGH
 call high_finish
 jnc .high_restored
 mov word [status],1
 mov [status+2],ax
.high_restored:
%endif
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
%ifdef STATUS_RUNNER_HIGH
; Lab-only high wrapper. Keep the application on ordinary first-fit memory.
; Relocate and compare the complete owned environment, including its opaque
; trailer, before freeing the low copy. Never borrow or free a parent's block.
high_prepare:
 mov ax,cs
 cmp ax,0a000h
 jb .invalid
 mov ax,5800h
 int 21h
 jc .return
 mov [saved_strategy],ax
 mov word [strategy_held],1
 mov ax,5802h
 int 21h
 jc .return
 cmp al,1
 jne .invalid
 mov ax,[2ch]
 cmp ax,10h
 jb .invalid
 mov [old_environment],ax
 dec ax
 mov es,ax
 cmp byte [es:0],'M'
 je .mcb
 cmp byte [es:0],'Z'
 jne .invalid
.mcb:
 mov ax,cs
 cmp [es:1],ax
 jne .invalid
 mov bx,[es:3]
 or bx,bx
 jz .invalid
 cmp bx,4095
 ja .invalid
 mov [environment_paragraphs],bx
 mov ax,5801h
 mov bx,40h ; Upper-memory-only first fit; verify the returned segment too.
 int 21h
 jc .return
 mov bx,[environment_paragraphs]
 mov ah,48h
 int 21h
 jc .return
 mov [new_environment],ax
 cmp ax,0a000h
 jb .invalid
 mov es,ax
 push ds
 mov ds,[old_environment]
 xor si,si
 xor di,di
 mov cx,[cs:environment_paragraphs]
 shl cx,1
 shl cx,1
 shl cx,1
 cld
 rep movsw
 xor si,si
 xor di,di
 mov cx,[cs:environment_paragraphs]
 shl cx,1
 shl cx,1
 shl cx,1
 repe cmpsw
 pop ds
 jne .invalid
 mov word [environment_compared],1
 mov ax,[new_environment]
 mov [2ch],ax
 mov es,[old_environment]
 mov ah,49h
 int 21h
 jc .return
 mov ax,5801h
 xor bx,bx
 int 21h
 jc .return
 push cs
 pop es
 clc
.return:
 ret
.invalid:
 mov ax,8
 stc
 ret
high_finish:
 cmp word [strategy_held],1
 jne .done
 mov bx,[saved_strategy]
 mov ax,5801h
 int 21h
 jc .return
 mov ax,5800h
 int 21h
 jc .return
 cmp ax,[saved_strategy]
 jne .invalid
 mov word [strategy_held],0
 mov dx,environment_report
 xor cx,cx
 mov ah,3ch
 int 21h
 jc .return
 mov bx,ax
 mov dx,environment_proof
 mov cx,12
 mov ah,40h
 int 21h
 jc .close_error
 cmp ax,12
 jne .close_error
 mov ah,3eh
 int 21h
 ret
.close_error:
 mov ah,3eh
 int 21h
.invalid:
 mov ax,8
 stc
.return:
 ret
.done:
 clc
 ret
environment_report: db 'D:\ENVPROOF.BIN',0
environment_proof: dw 5354h,1
old_environment: dw 0
new_environment: dw 0
environment_paragraphs: dw 0
environment_compared: dw 0
saved_strategy: dw 0
strategy_held: dw 0
%endif
parameters: dw 0,80h,0,5ch,0,6ch,0
status: dw 0,0,0ffffh
exec_ax: dw 0
exec_failed: db 0
program: db 'C:\TERMINAL.EXE',0
report: db 'D:\EXITCODE.BIN',0
align 2
times 256 db 0
stack_top:
