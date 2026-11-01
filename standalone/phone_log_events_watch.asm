; Passive diagnostic observer: timer samples of stable foreground publications,
; plus a final sample at parent's INT21/4C before DOS frees its memory.
; No DOS/UART/key calls or application writes inside either handler.
BITS 16
CPU 8086
ORG 100h
%ifdef DISK_ATTEMPTS_OFFSET
%define RECORD_BYTES 720
%else
%define RECORD_BYTES 716
%endif
%define RECORD_LIMIT 8
%ifdef DISK_ATTEMPTS_OFFSET
%define SAMPLE_BYTES (22+RECORD_BYTES*RECORD_LIMIT)
%else
%define SAMPLE_BYTES (20+RECORD_BYTES*RECORD_LIMIT)
%endif
jmp start
old_timer: dd 0
old_dos: dd 0
old_irq_segment: dw 0
sample: dw 0x4c45,0,0,0,0,0,0,0,0,0
records: times RECORD_BYTES*RECORD_LIMIT db 0
%ifdef DISK_ATTEMPTS_OFFSET
retry_notice: dw 0
retry_text: db 'Call log retry required',0
%endif
%macro save 0
 pushf
 push bp
 mov bp,sp
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
%endmacro
%macro restore 0
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 popf
%endmacro
timer_handler:
 save
 inc word [sample+2]
 xor ax,ax
 mov es,ax
 cmp word [es:IRQ_VECTOR*4],ISR_OFFSET
 jne .done
 mov bx,[es:IRQ_VECTOR*4+2]
 cmp bx,[old_irq_segment]
 je .done
 sub bx,ISR_SEGMENT
 jc .done
 cmp word [sample+8],0
 jne .known
 mov [sample+8],bx
 mov ax,bx
 add ax,DATA_SEGMENT
 mov [sample+10],ax
 mov ax,bx
 add ax,QUEUE_SEGMENT
 mov [sample+12],ax
.known:
 cmp bx,[sample+8]
 jne .done
%ifdef DISK_ATTEMPTS_OFFSET
 call scan_retry_notice
%endif
 mov dx,1
 call capture
.done:
 restore
 jmp far [cs:old_timer]
dos_handler:
 save
 cmp ah,4ch
 jne .done
 cmp word [sample+8],0
 je .done
 ; Extra PUSHF/saved BP put interrupt return CS at BP+6.
 mov bx,[ss:bp+6]
 cmp bx,[sample+8]
 jne .done
 mov bx,ss
 cmp bx,[sample+10]
 jne .done
 and ax,255
 mov [sample+18],ax
 mov dx,2
 call capture
.done:
 restore
 jmp far [cs:old_dos]
; DX1 timer, DX2 final. All scratch registers belong to handler's saved frame.
capture:
 mov ax,[sample+10]
 mov es,ax
 cmp word [es:LIFECYCLE_OFFSET],0x4c45
 jne .done
 cmp word [es:LIFECYCLE_OFFSET+10],0
 jne .done
 mov ax,[es:EPOCH_OFFSET]
 cmp dx,2
 je .changed
 cmp ax,[sample+14]
 je .done
.changed:
 mov bx,[sample+12]
 mov es,bx
 cmp word [es:QUEUE_OFFSET],0x514d
 jne .done
 cmp word [es:QUEUE_OFFSET+2],0
 jne .done
 mov [sample+14],ax
 mov bp,dx
 mov ax,[sample+4]
 cmp ax,RECORD_LIMIT-1
 jb .slot
 cmp dx,2
 je .last
 inc word [sample+16]
 ret
.last:
 mov ax,RECORD_LIMIT-1
.slot:
 mov cx,RECORD_BYTES
 mul cx
 mov di,records
 add di,ax
 mov [di],bp
 mov ax,[sample+10]
 mov es,ax
 mov ax,[es:EPOCH_OFFSET]
 mov [di+2],ax
 mov ax,[es:EVENT_STATUS_OFFSET]
 mov [di+4],ax
 mov ax,[es:CONNECTION_STATE_OFFSET]
 mov [di+6],ax
 mov ax,[es:CONNECTION_STATUS_OFFSET]
 mov [di+8],ax
 mov ax,[es:STARTUP_STATUS_OFFSET]
 mov [di+10],ax
 add di,12
 mov si,LIFECYCLE_OFFSET
 mov cx,38
.life:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .life
 mov ax,[sample+12]
 mov es,ax
 mov si,QUEUE_OFFSET
 mov cx,666
.queue:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .queue
%ifdef DISK_ATTEMPTS_OFFSET
 mov ax,[sample+10]
 mov es,ax
 mov ax,[es:DISK_ATTEMPTS_OFFSET]
 mov [di],ax
 mov ax,[es:DISK_STATUS_OFFSET]
 mov [di+2],ax
%endif
 cmp word [sample+4],RECORD_LIMIT
 jae .counted
 inc word [sample+4]
.counted:
 cmp bp,2
 jne .done
 mov word [sample+6],1
.done:
 ret
%ifdef DISK_ATTEMPTS_OFFSET
; Actual bottom-row text is observed throughout the call; transport notices
; may legitimately replace this warning before the final shutdown frame.
scan_retry_notice:
 cmp word [retry_notice],0
 jne .done
 mov ax,0xb800
 mov es,ax
 mov di,3840
.next:
 mov bx,di
 mov si,retry_text
.match:
 mov al,[si]
 or al,al
 jz .found
 cmp al,[es:bx]
 jne .advance
 inc si
 add bx,2
 cmp bx,4000
 jb .match
.advance:
 add di,2
 cmp di,4000
 jb .next
 ret
.found:
 mov word [retry_notice],1
.done:
 ret
%endif
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_timer],bx
 mov [old_timer+2],es
 mov ax,3521h
 int 21h
 mov [old_dos],bx
 mov [old_dos+2],es
 xor ax,ax
 mov es,ax
 mov ax,[es:IRQ_VECTOR*4+2]
 mov [old_irq_segment],ax
 mov dx,timer_handler
 mov ax,251ch
 int 21h
 mov dx,dos_handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,timer_handler
 jne failed
 cmp word [es:sample],0x4c45
 jne failed
 mov ax,[es:old_dos]
 mov [old_dos],ax
 mov ax,[es:old_dos+2]
 mov [old_dos+2],ax
 mov ax,[es:old_timer]
 mov [old_timer],ax
 mov ax,[es:old_timer+2]
 mov [old_timer+2],ax
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
 push es
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 pop es
 mov dx,[es:old_timer]
 mov ax,[es:old_timer+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 ; Both hooks must be restored exactly before accepting/writing the witness.
 mov ax,3521h
 int 21h
 cmp bx,[old_dos]
 jne failed
 mov ax,es
 cmp ax,[old_dos+2]
 jne failed
 mov ax,351ch
 int 21h
 cmp bx,[old_timer]
 jne failed
 mov ax,es
 cmp ax,[old_timer+2]
 jne failed
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
filename: db 'D:\PLSTATE.BIN',0
buffer: times SAMPLE_BYTES db 0
