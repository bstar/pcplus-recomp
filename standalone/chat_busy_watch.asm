; Passive INT16 observer. Only reads parent state and BIOS queue; never injects
; keys, changes product memory, reads UART or replaces BIOS behavior.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
old_bell_vector: dw 0,0
sample: dw 0x4257,0,0,0,0,0,0,0,0,0,0,0,0,0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .done
 ; Map-derived relative paragraphs identify the exact loaded parent.
 add ax,FROZEN_DELTA
 mov es,ax
 cmp word [es:5],0x4f4c
 jne .done
 cmp word [es:7],0x4343
 jne .done
 cmp word [es:13],0x0104
 jne .done
 cmp word [es:13202],4 ; foreground module STEP
 jne .cleanup
 cmp word [es:12650],1 ; session+362, active TEXT
 jne .cleanup
 cmp word [OWNER_OFF],2
 jne .cleanup
 cmp word [PARSER_OFF],1
 jne .cleanup
 cmp word [WAIT_OFF],1
 jne .cleanup
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 test word [cs:sample+2],1
 jnz .have_first
 mov [cs:sample+14],ax
.have_first:
 mov [cs:sample+16],ax
 or word [cs:sample+2],1
 inc word [cs:sample+4]
 mov ax,[STATUS_OFF]
 cmp ax,[cs:sample+26]
 jbe .status_counted
 mov [cs:sample+26],ax
.status_counted:
 mov ax,[DEFERRED_OFF]
 cmp ax,[cs:sample+22]
 jbe .deferred_counted
 mov [cs:sample+22],ax
.deferred_counted:
 or ax,ax
 jz .no_deferred
 or word [cs:sample+2],8
.no_deferred:
 mov bx,[es:0x1a]
 cmp bx,[es:0x1c]
 je .done
 mov ax,[es:bx]
 mov [cs:sample+20],ax
 cmp ax,0x2d58 ; queued uppercase X, before BIOS dequeue
 jne .done
 or word [cs:sample+2],2
 inc word [cs:sample+6]
 mov [cs:sample+10],bx
 mov ax,[es:0x1c]
 mov [cs:sample+12],ax
 jmp .done
.cleanup:
 test word [cs:sample+2],1
 jz .done
 cmp word [OWNER_OFF],0
 jne .done
 cmp word [PARSER_OFF],0
 jne .done
 cmp word [WAIT_OFF],0
 jne .done
 mov ax,[DEFERRED_OFF]
 mov [cs:sample+20],ax ; retained FIFO must be empty once Chat is retired
 test word [cs:sample+2],4
 jnz .retired
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov [cs:sample+18],ax
.retired:
 or word [cs:sample+2],4
 inc word [cs:sample+8]
.done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
bell_handler:
 pushf
 push ax
 push dx
 push es
 cmp ax,0x0e07
 jne .done
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .done
 add ax,FROZEN_DELTA
 mov es,ax
 cmp word [es:5],0x4f4c
 jne .done
 cmp word [es:13],0x0104
 jne .done
 cmp word [OWNER_OFF],2
 jne .done
 inc word [cs:sample+24] ; BIOS bell request, not acoustic/hardware proof.
.done:
 pop es
 pop dx
 pop ax
 popf
 jmp far [cs:old_bell_vector]
resident_end:
start:
 mov ax,0x3516
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ax,0x3510
 int 21h
 mov [old_bell_vector],bx
 mov [old_bell_vector+2],es
 mov dx,bell_handler
 mov ax,0x2510
 int 21h
 mov dx,handler
 mov ax,0x2516
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4257
 jne failed
 mov ax,[es:old_bell_vector]
 mov [expected_bell],ax
 mov ax,[es:old_bell_vector+2]
 mov [expected_bell+2],ax
 mov ax,[es:old_vector]
 mov [expected_key],ax
 mov ax,[es:old_vector+2]
 mov [expected_key+2],ax
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,28
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 push es
 mov dx,[es:old_bell_vector]
 mov ax,[es:old_bell_vector+2]
 push ds
 mov ds,ax
 mov ax,0x2510
 int 21h
 pop ds
 pop es
 mov dx,[es:old_vector]
 mov ax,[es:old_vector+2]
 push ds
 mov ds,ax
 mov ax,0x2516
 int 21h
 pop ds
 mov ax,0x3510
 int 21h
 cmp bx,[expected_bell]
 jne failed
 mov ax,es
 cmp ax,[expected_bell+2]
 jne failed
 mov ax,0x3516
 int 21h
 cmp bx,[expected_key]
 jne failed
 mov ax,es
 cmp ax,[expected_key+2]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,28
 mov ah,40h
 int 21h
 jc failed
 cmp ax,28
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\BUSYVIEW.BIN',0
buffer: times 28 db 0
expected_bell: dw 0,0
expected_key: dw 0,0
