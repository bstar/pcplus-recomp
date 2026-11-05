; Passive stable VGA/BDA observer. No DOS/BIOS calls or product writes in ISR.
; File header: magic,count,ticks,restored (8bytes); eight records each contain
; cursor,shape (4bytes), then4000video bytes. A final4bytes hold the independent
; pre-popup BIOS cursor/shape. No scheduler words are interleaved with records.
BITS 16
CPU 8086
ORG 100h
jmp start
old: dw 0,0
last: dw 0
last_cursor: dw 0
last_shape: dw 0
stable: dw 0
prior: dw 0xffff
prior_cursor: dw 0xffff
prior_shape: dw 0xffff
armed: dw 0
cursor: dw 0
shape: dw 0
before_cursor: dw 0
before_shape: dw 0
sample: dw 0x5056,0,0,0
frames: times 32032 db 0
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
 cmp word [sample+2],8
 jae .done
 mov ax,40h
 mov es,ax
 mov ax,[es:50h]
 mov [cursor],ax
 mov ax,[es:60h]
 mov [shape],ax
 mov ax,0xb800
 mov es,ax
 cmp word [armed],0
 jne .sum_start
 cmp word [es:806],0x03b5
 jne .before
 cmp word [es:1126],0x034e
 jne .before
 mov word [armed],1
.sum_start:
 xor dx,dx
 xor si,si
 mov cx,2000
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 cmp dx,[last]
 jne .changed
 mov ax,[cursor]
 cmp ax,[last_cursor]
 jne .changed
 mov ax,[shape]
 cmp ax,[last_shape]
 jne .changed
 inc word [stable]
 cmp word [stable],2
 jb .done
 cmp dx,[prior]
 jne .capture
 mov ax,[cursor]
 cmp ax,[prior_cursor]
 jne .capture
 mov ax,[shape]
 cmp ax,[prior_shape]
 je .done
.capture:
 mov [prior],dx
 mov ax,[cursor]
 mov [prior_cursor],ax
 mov ax,[shape]
 mov [prior_shape],ax
 mov ax,[sample+2]
 mov bx,4004
 mul bx
 mov di,frames
 add di,ax
 mov ax,[cursor]
 mov [di],ax
 mov ax,[shape]
 mov [di+2],ax
 add di,4
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 inc word [sample+2]
 jmp .done
.changed:
 mov [last],dx
 mov ax,[cursor]
 mov [last_cursor],ax
 mov ax,[shape]
 mov [last_shape],ax
 mov word [stable],0
 jmp .done
.before:
 ; Capture the live BBS baseline, not an intervening menu's hidden cursor.
 cmp word [es:0],0x0746 ; FIRST BYTE SAFE
 jne .done
 cmp word [es:2],0x0749
 jne .done
 mov ax,[cursor]
 mov [before_cursor],ax
 mov ax,[shape]
 mov [before_shape],ax
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
 cmp word [es:sample],0x5056
 jne failed
 mov si,sample
 mov di,report
 mov cx,32040
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov ax,[es:before_cursor]
 mov [report+32040],ax
 mov ax,[es:before_shape]
 mov [report+32042],ax
 mov dx,[es:old]
 mov [expected_off],dx
 mov ax,[es:old+2]
 mov [expected_seg],ax
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov ax,351ch
 int 21h
 cmp bx,[expected_off]
 jne failed
 mov ax,es
 cmp ax,[expected_seg]
 jne failed
 mov word [report+6],1
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,report
 mov cx,32044
 mov ah,40h
 int 21h
 jc failed
 cmp ax,32044
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\EDITVIEW.BIN',0
expected_off: dw 0
expected_seg: dw 0
report: times 32044 db 0
