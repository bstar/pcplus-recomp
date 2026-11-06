; Passive actual-viewer/carrier witness. BIOS timer reads only; no UART/DOS in ISR.
bits 16
cpu 8086
org 100h
jmp start
old dd 0
report:
 ; magic/version/ticks,painted-page/offline-close/released/redial flags,
 ; loss tick,load segment,last connection state,phase/active/handle/claim at
 ; offline close,last connection status,file phase at offline close.
 dw 5658h,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
frame times 4000 db 0
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
 inc word [report+4]
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
 ; The vector-derived base is the MZ load segment,16 paragraphs above PSP.
 mov ax,[es:PROCESS_PSP]
 add ax,16
 cmp ax,bx
 jne .done
 mov [report+16],bx
 mov ax,[es:CONNECTION_STATUS]
 mov [report+28],ax
 mov ax,[es:CONNECTION_STATE]
 mov [report+18],ax
 add bx,VIEWER_SEGMENT
 mov es,bx
%ifdef EXTERNAL_VIEWER
 cmp word [es:VIEWER_STATE],5658h
%else
 cmp word [es:VIEWER_STATE],5644h
%endif
 jne .done
 cmp word [es:VIEWER_STATE+2],1
 jne .inactive
%ifdef EXTERNAL_VIEWER
 cmp word [es:VIEWER_STATE+4],0
%else
 cmp word [es:VIEWER_STATE+4],3
%endif
 jne .done
 cmp ax,6
 jne .done
 cmp word [report+6],1
 je .done
 ; Require actual painted page cells, rather than merely a published phase.
 push es
 mov ax,0b800h
 mov es,ax
%ifdef EXTERNAL_VIEWER
 cmp word [es:1934],0b45h
 jne .not_painted
 cmp word [es:1936],0b6eh
%else
 cmp word [es:0],074ch
 jne .not_painted
 cmp word [es:3842],7148h
%endif
 jne .not_painted
 mov word [report+6],1
 xor si,si
 mov di,frame
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add di,2
 add si,2
 loop .copy
.not_painted:
 pop es
 jmp .done
.inactive:
 cmp word [report+6],1
 jne .done
 or ax,ax
 jnz .reconnected
 cmp word [report+28],6
 jne .done
 cmp word [report+8],1
 je .done
 mov word [report+8],1
 mov ax,[report+4]
 mov [report+14],ax
 mov ax,[es:VIEWER_STATE+4]
 mov [report+20],ax
 mov ax,[es:VIEWER_STATE+2]
 mov [report+22],ax
%ifdef EXTERNAL_VIEWER
 mov ax,[es:VIEWER_STATE]
 mov [report+24],ax
 mov ax,[es:VIEWER_STATE+4]
 mov [report+26],ax
 xor ax,ax
 mov [report+30],ax
 cmp word [report+24],5658h
 jne .done
 cmp word [report+26],0
 jne .done
%else
 mov ax,[es:FILE_STATE+18]
 mov [report+24],ax
 mov ax,[es:FILE_STATE+20]
 mov [report+26],ax
 mov ax,[es:FILE_STATE+6]
 mov [report+30],ax
 cmp word [report+24],0ffffh
 jne .done
 cmp word [report+26],0
 jne .done
 cmp word [report+30],3
 jne .done
%endif
 mov word [report+10],1
 jmp .done
.reconnected:
 cmp word [report+10],1
 jne .done
 cmp ax,6
 jne .done
 mov word [report+12],1
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
 jne .collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
.collect:
 cmp bx,handler
 jne .failed
 cmp word [es:report],5658h
 jne .failed
 ; Copy once with interrupts disabled, then unhook before writing our report.
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
 mov ax,[es:old]
 mov [expected_offset],ax
 mov ax,[es:old+2]
 mov [expected_segment],ax
 push ds
 mov dx,[es:old]
 mov ds,[es:old+2]
 mov ax,251ch
 int 21h
 pop ds
 mov ax,351ch
 int 21h
 cmp bx,[expected_offset]
 jne .failed
 mov ax,es
 cmp ax,[expected_segment]
 jne .failed
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc .failed
 mov bx,ax
 mov dx,buffer
 mov cx,4032
 mov ah,40h
 int 21h
 jc .failed
 cmp ax,4032
 jne .failed
 mov ah,3eh
 int 21h
 jc .failed
 mov ax,4c00h
 int 21h
.failed:
 mov ax,4c01h
 int 21h
name db 'D:\VCSTATE.BIN',0
expected_offset dw 0
expected_segment dw 0
buffer times 4032 db 0
