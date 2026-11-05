; Passive test-only timer capture: live before, target UI, live after. No IO in ISR.
BITS 16
CPU 8086
ORG 100h
jmp start
old: dw 0,0
sample: dw 5656h,0,0,0,0,0,0,0,0
frames: times 12000 db 0
last: dw 0
stable: dw 0
seen_next: dw 0
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
 inc word [sample+4]
 test word [sample+2],4
 jnz .done
 mov ax,0b800h
 mov es,ax
 test word [sample+2],1
 jz .live_before
 test word [sample+2],2
 jnz .live_after
%if WATCH_KIND = 1
 cmp word [es:1618],0bb5h
 jne .done
 cmp word [es:1980],0a20h
 jne .done
%elif WATCH_KIND = 4
 cmp word [es:1934],0b46h
 jne .done
 cmp word [es:1936],0b49h
 jne .done
%else
 cmp word [es:3842],7148h ; Footer Home
 jne .done
%if WATCH_KIND = 3
 cmp word [es:0],074ch
 jne .done
 cmp word [es:4],0732h
 jne .done
 cmp word [es:6],0735h
 jne .done
%elif WATCH_KIND = 5
 cmp word [es:0],0754h
 jne .done
 cmp word [es:6],0709h
 jne .done
%elif WATCH_KIND = 6
 cmp word [es:0],0720h
 jne .done
%elif WATCH_KIND = 7
 cmp word [es:4],0732h
 jne .home_candidate
 cmp word [es:6],0735h
 jne .home_candidate
 mov word [seen_next],1
.home_candidate:
 cmp word [seen_next],1
 jne .done
 cmp word [es:4],0730h
 jne .done
 cmp word [es:6],0731h
 jne .done
%else
 cmp word [es:0],074ch
 jne .done
 cmp word [es:4],0730h
 jne .done
 cmp word [es:6],0731h
 jne .done
%endif
%endif
 mov bx,1
 jmp .candidate
.live_before:
 xor bx,bx
 jmp .live
.live_after:
 mov bx,2
%if WATCH_KIND = 8
 cmp word [es:3520],0755h
 jne .done
 cmp word [es:3522],0741h
 jne .done
%endif
.live:
 cmp word [es:0],0746h
 jne .done
 cmp word [es:2],0749h
 jne .done
 cmp word [es:4],0752h
 jne .done
 cmp word [es:1618],0bb5h
 je .done
.candidate:
 xor dx,dx
 xor si,si
 mov cx,2000
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 cmp dx,[last]
 je .same
 mov [last],dx
 mov word [stable],0
 jmp .done
.same:
 inc word [stable]
 cmp word [stable],2
 jb .done
 mov ax,bx
 shl bx,1
 shl bx,1
 push es
 mov cx,40h
 mov es,cx
 mov cx,[es:50h]
 mov [sample+6+bx],cx
 mov cx,[es:60h]
 mov [sample+8+bx],cx
 pop es
 mov bx,4000
 mul bx
 mov di,frames
 add di,ax
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 mov ax,1
 test word [sample+2],1
 jz .mark
 mov ax,2
 test word [sample+2],2
 jz .mark
 mov ax,4
.mark:
 or [sample+2],ax
 mov word [stable],0
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
 cmp word [es:sample],5656h
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,12018
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old]
 mov [expected_offset],dx
 mov ax,[es:old+2]
 mov [expected_segment],ax
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov ax,351ch
 int 21h
 cmp bx,[expected_offset]
 jne failed
 mov ax,es
 cmp ax,[expected_segment]
 jne failed
 or word [buffer+2],8
 mov ah,19h
 int 21h
 mov [buffer+12018],al
 mov si,buffer+12019
 xor dl,dl
 mov ah,47h
 int 21h
 jc failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,12083
 mov ah,40h
 int 21h
 jc failed
 cmp ax,12083
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\VIEWUI.BIN',0
expected_offset: dw 0
expected_segment: dw 0
buffer: times 12083 db 0
