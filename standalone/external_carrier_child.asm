; Owned DOS child: observe real modem carrier while the parent relinquishes UART.
; No product memory writes, serial commands, or synthetic terminal replies.
bits 16
cpu 8086
org 100h
%ifndef UART_BASE
%define UART_BASE 3e8h
%endif
jmp start
report:
 dw 0c156h,1
entry_flags: dw 0
entry_msr: dw 0
entry_mcr: dw 0
entry_ier: dw 0
saw_high: dw 0
saw_low: dw 0
elapsed: dw 0
child_segment: dw 0
exit_flags: dw 0
exit_msr: dw 0
exit_mcr: dw 0
exit_ier: dw 0
report_end:
started: dw 0
name: db 'D:\VLOSS.BIN',0
start:
 push cs
 pop ds
 mov ax,cs
 mov [child_segment],ax
 pushf
 pop word [entry_flags]
 mov dx,UART_BASE+6
 in al,dx
 xor ah,ah
 mov [entry_msr],ax
 mov dx,UART_BASE+4
 in al,dx
 mov [entry_mcr],ax
 mov dx,UART_BASE+1
 in al,dx
 mov [entry_ier],ax
%ifdef GRAPHICS_CHILD
 mov ax,13h
 int 10h
%endif
 mov ax,40h
 mov es,ax
 mov ax,[es:6ch]
 mov [started],ax
.wait:
 mov dx,UART_BASE+6
 in al,dx
 xor ah,ah
 mov [exit_msr],ax
 test al,80h
 jz .low
 mov word [saw_high],1
 jmp .clock
.low:
 cmp word [saw_high],1
 jne .clock
 mov word [saw_low],1
.clock:
 mov ax,[es:6ch]
 sub ax,[started]
 mov [elapsed],ax
 cmp word [saw_low],1
 je .record
 cmp ax,162 ; Bound the owned fixture even if the peer fails to disconnect.
 jae .record
 sti
 hlt
 jmp .wait
.record:
 pushf
 pop word [exit_flags]
 mov dx,UART_BASE+4
 in al,dx
 xor ah,ah
 mov [exit_mcr],ax
 mov dx,UART_BASE+1
 in al,dx
 mov [exit_ier],ax
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc .failed
 mov bx,ax
 mov dx,report
 mov cx,report_end-report
 mov ah,40h
 int 21h
 jc .failed
 cmp ax,report_end-report
 jne .failed
 mov ah,3eh
 int 21h
 jc .failed
 mov ax,4c00h
 int 21h
.failed:
 mov ax,4c01h
 int 21h
