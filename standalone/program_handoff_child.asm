; Synthetic child for live PROGRAM handoff. No vendor or user program is run.
BITS 16
CPU 8086
ORG 0x100
%ifndef PORT
%define PORT 0x3f8
%endif
%ifndef IRQ_VECTOR
%define IRQ_VECTOR 0x0c
%endif
start:
 push cs
 pop ds
 mov ax,0x3500+IRQ_VECTOR
 int 0x21
 mov [sample],bx
 mov [sample+2],es
 pushf
 cli
 mov dx,PORT+3
 in al,dx
 mov [sample+4],al
 and al,0x7f
 out dx,al
 mov dx,PORT+1
 in al,dx
 mov [sample+5],al
 mov dx,PORT+4
 in al,dx
 mov [sample+6],al
 mov dx,PORT+3
 mov al,[sample+4]
 or al,0x80
 out dx,al
 mov dx,PORT
 in al,dx
 mov [sample+7],al
 inc dx
 in al,dx
 mov [sample+8],al
 mov dx,PORT+3
 mov al,[sample+4]
 out dx,al
 in al,0x21
 mov [sample+9],al
 popf
 mov dx,sample_name
 call create
 mov dx,sample
 mov cx,10
 call write_close
 mov dx,arguments_name
 call create
 mov dx,0x80
 xor cx,cx
 mov cl,[0x80]
 add cx,2
 call write_close
 ; A child can take over the port. Leave it masked and changed to exercise the
 ; parent's real recovery, including overwriting this soon-freed IRQ target.
 mov dx,PORT+3
 mov al,0x80
 out dx,al
 mov dx,PORT
 mov al,24
 out dx,al
 inc dx
 xor al,al
 out dx,al
 mov dx,PORT+3
 mov al,0x1b
 out dx,al
 mov dx,PORT+4
 mov al,1
 out dx,al
 mov dx,child_irq
 mov ax,0x2500+IRQ_VECTOR
 int 0x21
 mov ax,0x13
 int 0x10
 mov ax,0x4c25
 int 0x21
child_irq:
 iret
create:
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 ret
write_close:
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,cx
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 ret
failed:
 mov ax,0x4cff
 int 0x21
sample_name: db 'D:\HANDOFF.BIN',0
arguments_name: db 'D:\HANDARG.BIN',0
sample: times 10 db 0
