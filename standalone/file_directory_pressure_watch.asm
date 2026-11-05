; Test-only passive VGA observer. ISR has no DOS/BIOS calls or product writes.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
sample: dw 0x4644,0,0
frame: times 4000 db 0
last_sum: dw 0
stable: dw 0
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
 test word [sample+2],1
 jnz .done
 mov ax,0xb800
 mov es,ax
%if WATCH_KIND = 1
 cmp word [es:1612],0x0bb5
 jne .done
%elif WATCH_KIND = 4
 cmp word [es:1664],0x0a46
 jne .done
%else
 cmp word [es:364],0x0746
 jne .done
%if WATCH_KIND = 2
 cmp word [es:3274],0x072d
 jne .done
%elif WATCH_KIND = 3
 cmp byte [es:684],'F'
 jne .done
 cmp byte [es:686],'1'
 jne .done
 cmp byte [es:688],'5'
 jne .done
%elif WATCH_KIND = 5
 cmp byte [es:0],'A'
 jne .done
 cmp byte [es:2],'A'
 jne .done
%endif
%endif
 xor dx,dx
 xor si,si
 mov cx,2000
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 cmp dx,[last_sum]
 je .same
 mov [last_sum],dx
 mov word [stable],0
 jmp .done
.same:
 inc word [stable]
 cmp word [stable],2
 jb .done
 mov di,frame
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 or word [sample+2],1
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
 cmp word [es:sample],0x4644
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,4006
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old_vector]
 mov [expected_offset],dx
 mov ax,[es:old_vector+2]
 mov [expected_segment],ax
 push ds
 mov ds,ax
 mov ax,0x251c
 int 21h
 pop ds
 mov ax,0x351c
 int 21h
 cmp bx,[expected_offset]
 jne failed
 mov ax,es
 cmp ax,[expected_segment]
 jne failed
 or word [buffer+2],2
 mov ah,0x19
 int 21h
 mov [buffer+4006],al
 mov si,buffer+4007
 xor dl,dl
 mov ah,0x47
 int 21h
 jc failed
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,4071
 mov ah,0x40
 int 21h
 jc failed
 cmp ax,4071
 jne failed
 mov ah,0x3e
 int 21h
 jc failed
 mov ax,0x4c00
 int 21h
failed:
 mov ax,0x4c01
 int 21h
filename: db 'D:\FILEVIEW.BIN',0
expected_offset: dw 0
expected_segment: dw 0
buffer: times 4071 db 0
