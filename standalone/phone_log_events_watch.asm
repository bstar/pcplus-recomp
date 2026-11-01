; Passive diagnostic observer: timer samples of stable foreground publications,
; plus a final sample at parent's INT21/4C before DOS frees its memory.
; No DOS/UART/key calls or application writes inside either handler.
BITS 16
CPU 8086
ORG 100h
%ifdef CONTROL_ACK_OFFSET
%define RECORD_BYTES 722
%elifdef DISK_ATTEMPTS_OFFSET
%define RECORD_BYTES 720
%else
%define RECORD_BYTES 716
%endif
%define RECORD_LIMIT 8
%ifdef CONTROL_ACK_OFFSET
%define SAMPLE_BYTES (4022+RECORD_BYTES*RECORD_LIMIT)
%elifdef DISK_ATTEMPTS_OFFSET
%define SAMPLE_BYTES (22+RECORD_BYTES*RECORD_LIMIT)
%else
%define SAMPLE_BYTES (20+RECORD_BYTES*RECORD_LIMIT)
%endif
%ifdef ASPECT_CHILD
%assign SAMPLE_BYTES SAMPLE_BYTES+18
%endif
%ifdef TRANSFER_WATCH
%assign SAMPLE_BYTES SAMPLE_BYTES+64
%endif
jmp start
old_timer: dd 0
old_dos: dd 0
old_irq_segment: dw 0
sample: dw 0x4c45,0,0,0,0,0,0,0,0,0
records: times RECORD_BYTES*RECORD_LIMIT db 0
%ifdef DISK_ATTEMPTS_OFFSET
retry_notice: dw 0
%ifdef CONTROL_ACK_OFFSET
control_frame: times 4000 db 0
%ifdef ASPECT_CHILD
child_watch: times 9 dw 0
%endif
%ifdef TRANSFER_WATCH
transfer_watch: times 32 dw 0
%endif
ui_title: db 'Telephone call log',0
ui_confirm: db 'Retry retained records? Y/N',0
ui_accepted: db 'Retry acknowledged; close to resume',0
ui_cancelled: db 'Retry canceled',0
ui_none: db 'No retry is pending',0
ui_recovery: db 'Recovery required: exit and inspect the log.',0
ui_footer: db 'R: retry   F5: refresh',0
%endif
retry_text: db 'Call log retry required',0
%endif
%ifdef ASPECT_CHILD
child_stopped: dw 0
%endif
%ifdef TRANSFER_WATCH
transfer_stopped: dw 0
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
%ifdef ASPECT_CHILD
 call capture_child
%endif
%ifdef TRANSFER_WATCH
 call capture_transfer
%endif
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
%ifdef ASPECT_CHILD
 mov bx,[child_watch+6]
 or bx,bx
 jz .parent
 mov dx,ss
 cmp dx,bx
 jne .parent
 sub bx,CHILD_DATA_SEG
 add bx,CHILD_EXIT_SEG
 cmp bx,[ss:bp+6]
 jne .parent
 mov word [child_watch+16],1
.parent:
%endif
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
%ifdef TRANSFER_WATCH
 call capture_transfer
 mov word [transfer_stopped],1
%endif
%ifdef ASPECT_CHILD
 mov word [child_stopped],1
%endif
 mov dx,2
 call capture
.done:
 restore
 jmp far [cs:old_dos]
%ifdef ASPECT_CHILD
; Parent is retained during EXEC. Identify the child by its exact live IRQ,
; then retain its DS until its verified DOS exit. Render RPC leases are brief
; and must not restrict observation of the cooperative script window.
; The parent-exit witness stops reads before DOS can free the parent image.
capture_child:
 cmp word [child_stopped],0
 jne .done
 cmp word [child_watch+16],0
 jne .done
 cmp word [sample+8],0
 je .done
 mov ax,[sample+8]
 add ax,PARENT_ASPECT_SEG
 mov es,ax
 mov bx,[es:PARENT_CHILD_DS]
 or bx,bx
 jz .done
 mov di,es
 cmp word [child_watch+6],0
 je .identify
 cmp bx,[child_watch+6]
 jne .done
 jmp .live
.identify:
 xor ax,ax
 mov es,ax
 cmp word [es:IRQ_VECTOR*4],CHILD_ISR_OFFSET
 jne .done
 mov ax,bx
 sub ax,CHILD_DATA_SEG
 add ax,CHILD_ISR_SEG
 cmp ax,[es:IRQ_VECTOR*4+2]
 jne .done
.live:
 mov es,bx
 inc word [child_watch]
 cmp word [child_watch+6],0
 jne .known
 mov [child_watch+6],bx
.known:
 mov [child_watch+8],bx
 cmp word [es:CHILD_ARMED],0
 je .window
 inc word [child_watch+2]
.window:
 mov ax,di
 mov es,ax
 cmp word [es:PARENT_WINDOW_ACTIVE],1
 jne .runtime
 cmp word [es:PARENT_WINDOW_VISIBLE],1
 jne .runtime
 inc word [child_watch+4]
.runtime:
 mov es,bx
 mov ax,[es:CHILD_ERROR]
 mov [child_watch+12],ax
 cmp word [es:CHILD_OPCODE],0d4h
 jne .carrier
 inc word [child_watch+14]
.carrier:
 mov dx,[es:CHILD_MSR_PORT]
 in al,dx
 test al,80h
 jnz .done
 inc word [child_watch+10]
.done:
 ret
%endif
%ifdef TRANSFER_WATCH
; Read-only parent/near storage snapshots while its DOS image is retained.
; Sample again at verified parent exit; never read after DOS frees it.
capture_transfer:
 cmp word [transfer_stopped],0
 jne .done
 mov ax,[sample+10]
 or ax,ax
 jz .done
 mov es,ax
 cmp word [es:TRANSFER_ACTIVE],0
 je .state
 inc word [transfer_watch]
 mov dx,[es:TRANSFER_MSR_PORT]
 in al,dx
 test al,80h
 jnz .state
 inc word [transfer_watch+2]
.state:
 mov ax,[es:TRANSFER_FAULT]
 mov [transfer_watch+4],ax
 mov ax,[es:TRANSFER_CLEANUP]
 mov [transfer_watch+6],ax
 mov ax,[es:TRANSFER_ACTIVE]
 mov [transfer_watch+8],ax
 mov ax,[es:TRANSFER_DIRECTION]
 mov [transfer_watch+10],ax
 mov ax,[es:TRANSFER_RX_DROPPED]
 mov [transfer_watch+12],ax
 mov ax,[es:TRANSFER_PENDING]
 mov [transfer_watch+14],ax
 mov bx,TRANSFER_DOWNLOAD
 mov di,transfer_watch+16
 mov cx,10
.download:
 mov ax,[es:bx]
 mov [di],ax
 add bx,2
 add di,2
 loop .download
 mov bx,TRANSFER_UPLOAD
 mov cx,14
.upload:
 mov ax,[es:bx]
 mov [di],ax
 add bx,2
 add di,2
 loop .upload
.done:
 ret
%endif
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
%ifdef CONTROL_ACK_OFFSET
 mov ax,[es:CONTROL_ACK_OFFSET]
 mov [di+4],ax
%endif
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
%ifdef CONTROL_ACK_OFFSET
 mov ax,0xb800
 mov es,ax
 mov si,retry_text
 mov di,3840
 mov dx,1
 call find_text
 mov si,ui_title
 mov di,0
 mov dx,2
 call find_text
 jnc .not_pane
 mov si,ui_footer
 mov di,3840
 mov dx,0
 call find_text
 jnc .not_pane
 xor si,si
 mov di,control_frame
 mov cx,4000
.copy_frame:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy_frame
.not_pane:
 mov si,ui_confirm
 mov di,2560
 mov dx,4
 call find_text
 mov si,ui_accepted
 mov di,2560
 mov dx,8
 call find_text
 mov si,ui_cancelled
 mov di,2560
 mov dx,16
 call find_text
 mov si,ui_none
 mov di,2560
 mov dx,32
 call find_text
 mov si,ui_recovery
 mov di,2560
 mov dx,64
 call find_text
 ret
; SI text, DI row start, DX latch bit (zero only probes), ES real video.
find_text:
 mov bp,si
.next:
 mov bx,di
 mov si,bp
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
 mov ax,di
 ; All callers search exactly the supplied80-column row.
 cmp dx,2
 je .title_end
 cmp di,2720
 jb .next
 cmp di,3840
 jb .missing
 cmp di,4000
 jb .next
 jmp .missing
.title_end:
 cmp di,160
 jb .next
.missing:
 clc
 ret
.found:
 or [retry_notice],dx
 stc
 ret
%else
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
