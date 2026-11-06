; Passive INT16 observer of real main: module identity, viewer ownership and
; actual live/visible frames. No injections, product writes or UART access.
BITS 16
CPU 8086
ORG 100h
%ifndef CHAT_API_VERSION
%define CHAT_API_VERSION 0x105
%endif
jmp start
old_vector: dw 0,0
sample: dw 0x5657,0,0,0,0,0,0,0
handler:
 pushf
 push ax
 push bx
 push dx
 push ds
 push es
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 jne .done
 add ax,FROZEN_DELTA
 mov es,ax
 cmp word [es:5],0x4f4c
 jne .done
 cmp word [es:7],0x4343
 jne .done
 cmp word [es:13],CHAT_API_VERSION
 jne .done
 cmp word [OWNER_OFF],1
 jne .chat
 cmp word [VIEW_OFF],1
 jne .done
 push es
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [cs:sample+10],ax
 pop es
 mov ax,ss
 add ax,LIVE_DELTA
 mov es,ax
 test word [cs:sample+2],1
 jnz .viewer_seen
 cmp byte [es:LIVE_OFF+REMOTE_OFF],32
 jne .viewer_seen
 or word [cs:sample+2],16 ; The remote pane was empty at viewer entry.
.viewer_seen:
 or word [cs:sample+2],1
 inc word [cs:sample+4]
 mov bx,LIVE_OFF
 jmp .remote
.chat:
 cmp word [OWNER_OFF],2
 jne .done
 cmp word [VIEW_OFF],0
 jne .done
 mov ax,0xb800
 mov es,ax
 xor bx,bx
.remote:
 cmp byte [es:bx+REMOTE_OFF],'R'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+2],'X'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+4],'L'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+6],'I'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+8],'V'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+10],'E'
 jne .done
 cmp byte [es:bx+REMOTE_OFF+12],0xf0
 jne .done
 cmp byte [es:bx+LOCAL_OFF],'A'
 jne .done
 cmp byte [es:bx+LOCAL_OFF+2],'B'
 jne .done
 cmp word [OWNER_OFF],1
 jne .resumed
 or word [cs:sample+2],2
 inc word [cs:sample+6]
 jmp .done
.resumed:
 or word [cs:sample+2],4
 inc word [cs:sample+8]
.done:
 pop es
 pop ds
 pop dx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
resident_end:
start:
 mov ax,0x3516
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x2516
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x5657
 jne failed
 mov ax,[es:old_vector]
 mov [expected_vector],ax
 mov ax,[es:old_vector+2]
 mov [expected_vector+2],ax
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,16
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
 mov ax,0x2516
 int 21h
 pop ds
 mov ax,0x3516
 int 21h
 cmp bx,[expected_vector]
 jne failed
 mov ax,es
 cmp ax,[expected_vector+2]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,16
 mov ah,40h
 int 21h
 jc failed
 cmp ax,16
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\CHATVIEW.BIN',0
buffer: times 16 db 0
expected_vector: dw 0,0
