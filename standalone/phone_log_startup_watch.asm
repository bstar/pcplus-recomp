; Passive test-only INT1C observer. Derive the loaded MZ base from its real
; installed UART IRQ vector, then read the accepted queue/status once. No DOS,
; UART IO, keyboard injection or writes into application memory in the handler.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dd 0
old_irq_segment: dw 0
sample: dw 0x4c53,0,0,0,0,0,0
queue: times 666 db 0
%ifdef CLAIM_OFFSET
claim: times 74 db 0
%define SAMPLE_BYTES 754
%else
%define SAMPLE_BYTES 680
%endif
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 cld
 inc word [sample+4]
 cmp word [sample+2],0
 jne .done
 xor ax,ax
 mov es,ax
 cmp word [es:IRQ_VECTOR*4],ISR_OFFSET
 jne .done
 mov bx,[es:IRQ_VECTOR*4+2]
 cmp bx,[old_irq_segment]
 je .done
 sub bx,ISR_SEGMENT
 jc .done
 mov [sample+6],bx
 mov ax,bx
 add ax,DATA_SEGMENT
 mov es,ax
 mov [sample+10],ax
 mov ax,[es:STATUS_OFFSET]
 mov [sample+8],ax
 mov ax,bx
 add ax,QUEUE_SEGMENT
 mov es,ax
 cmp word [es:QUEUE_OFFSET],0x514d
 jne .done
 mov [sample+12],ax
 mov si,QUEUE_OFFSET
 mov di,queue
 mov cx,666
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
%ifdef CLAIM_OFFSET
 mov ax,[sample+10]
 mov es,ax
 mov si,CLAIM_OFFSET
 mov di,claim
 mov cx,74
.copy_claim:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy_claim
%endif
 mov word [sample+2],1
.done:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 xor ax,ax
 mov es,ax
 mov ax,[es:IRQ_VECTOR*4+2]
 mov [old_irq_segment],ax
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4c53
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,SAMPLE_BYTES
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old_vector]
 mov ax,[es:old_vector+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,SAMPLE_BYTES
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,SAMPLE_BYTES
 jne .close_failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
.close_failed:
 mov ah,3eh
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\PLSTART.BIN',0
buffer: times SAMPLE_BYTES db 0
