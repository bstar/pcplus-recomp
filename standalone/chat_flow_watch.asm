; Passive INT16 observer. Only reads parent state and BIOS queue; never injects
; keys, changes product memory, reads UART or replaces BIOS behavior.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
sample: dw 0x4657,0,0,0,0,0,0,0
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
 cmp word [es:13],0x0104
 jne .done
 cmp word [OWNER_OFF],2
 jne .done
 cmp word [es:12650],1
 jne .finished
 cmp word [PAUSED_OFF],1
 jne .done
 cmp word [es:12656],2 ; pending TEXT TX, rather than its configured pause
 jne .done
 cmp word [es:12658],'T'
 jne .done
 or word [cs:sample+2],1
 inc word [cs:sample+4]
 mov ax,0xb800
 mov es,ax
 cmp byte [es:2880],'R'
 jne .done
 cmp byte [es:2882],'X'
 jne .done
 cmp byte [es:2884],'D'
 jne .done
 or word [cs:sample+2],2
 inc word [cs:sample+6]
 jmp .done
.finished:
 test word [cs:sample+2],3
 jz .done
 cmp word [PAUSED_OFF],0
 jne .done
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
 cmp word [es:sample],0x4657
 jne failed
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
filename: db 'D:\FLOWVIEW.BIN',0
buffer: times 16 db 0
