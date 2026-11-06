; Passive timer observer: VGA/BDA reads only, no product/UART/keyboard writes.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
sample: dw 0x4c54,0,0,0
pause_frame: times 4000 db 0
echo_frame: times 4000 db 0
handler:
 pushf
 push ax
 push cx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 mov ax,0xb800
 mov es,ax
 inc word [sample+4]
 cmp byte [es:3114],'L' ; LOCAL, row19 col37
 jne .done
 cmp byte [es:3200],'A'
 jne .done
 cmp byte [es:3202],'B'
 jne .done
 cmp byte [es:2880],'R' ; remote row18 begins RXD
 jne .done
 cmp byte [es:2882],'X'
 jne .done
 cmp byte [es:2884],'D'
 jne .done
 cmp byte [es:3204],'C'
 je .echo
 test word [sample+2],1
 jnz .done
 mov di,pause_frame
 call capture
 or word [sample+2],1
 jmp .done
.echo:
 test word [sample+2],2
 jnz .done
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 cmp ax,0x1400 ; module restores the unchanged local pane cursor
 jne .done
 mov [sample+6],ax
 mov ax,0xb800
 mov es,ax
 mov di,echo_frame
 call capture
 or word [sample+2],2
.done:
 pop es
 pop ds
 pop di
 pop si
 pop cx
 pop ax
 popf
 jmp far [cs:old_vector]
capture:
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 ret
resident_end:
start:
 mov ax,0x351c
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x251c
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4c54
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,8008
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
 mov ax,0x251c
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,8008
 mov ah,40h
 int 21h
 jc failed
 cmp ax,8008
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\LIVEVIEW.BIN',0
buffer: times 8008 db 0
