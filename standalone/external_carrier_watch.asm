; Read-only timer witness of the live, reconnected parent before it exits.
bits 16
cpu 8086
org 100h
jmp start
old: dd 0
report: dw 0ca56h,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
frame: times 4000 db 0
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
 inc word [report+4]
 cmp word [report+6],1
 je .done
 xor ax,ax
 mov es,ax
 cmp word [es:13*4],ISR_OFFSET
 jne .done
 mov bx,[es:13*4+2]
 sub bx,ISR_SEGMENT
 jc .done
 mov ax,bx
 add ax,DATA_SEGMENT
 mov es,ax
 mov ax,[es:PROCESS_PSP]
 add ax,16
 cmp ax,bx
 jne .done
 cmp word [es:CONNECTION_STATE],6
 jne .done
 push es
 mov ax,0b800h
 mov es,ax
 cmp word [es:320],074bh ; KEYOK, only sent after second-connection input.
 jne .not_ready
 cmp word [es:322],0745h
 jne .not_ready
 cmp word [es:324],0759h
 jne .not_ready
 cmp word [es:326],074fh
 jne .not_ready
 cmp word [es:328],074bh
 jne .not_ready
 pop es
 mov [report+8],bx
 mov ax,[es:CONNECTION_STATE]
 mov [report+10],ax
 mov ax,[es:PROGRAM_ACTIVE]
 mov [report+12],ax
 mov ax,[es:PROGRAM_PENDING]
 mov [report+14],ax
 add bx,EXTERNAL_SEGMENT
 mov es,bx
 mov ax,[es:EXTERNAL_STATE]
 mov [report+16],ax
 mov ax,[es:EXTERNAL_STATE+2]
 mov [report+18],ax
 mov ax,[es:EXTERNAL_STATE+4]
 mov [report+20],ax
 mov ax,40h
 mov es,ax
 mov ax,[es:49h]
 mov [report+22],ax
 xor ax,ax
 mov al,[es:84h]
 inc ax
 mov [report+24],ax
 mov ax,[es:50h]
 mov [report+26],ax
 mov ax,[es:60h]
 mov [report+28],ax
 mov ax,[es:85h]
 mov [report+30],ax
 mov ax,0b800h
 mov es,ax
 xor si,si
 mov di,frame
 mov cx,2000
 cld
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 mov word [report+6],1
 jmp .done
.not_ready:
 pop es
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
 jmp far [cs:old]
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:report],0ca56h
 jne failed
 pushf
 cli
 mov si,report
 mov di,buffer
 mov cx,4032
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old]
 mov [expected],dx
 mov ax,[es:old+2]
 mov [expected+2],ax
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov ax,351ch
 int 21h
 cmp bx,[expected]
 jne failed
 mov ax,es
 cmp ax,[expected+2]
 jne failed
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,4032
 mov ah,40h
 int 21h
 jc failed
 cmp ax,4032
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
expected: dd 0
name: db 'D:\VACT.BIN',0
buffer: times 4032 db 0
