; Independent test-only INT1C observer: records unique redisplay rows/footers.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
sample: dw 0x4452,0,0
frames: times 32*320 db 0
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
 mov ax,0xb800
 mov es,ax
 cmp word [es:2],0x1f50 ;P
 jne .done
 cmp word [es:4],0x1f43 ;C
 jne .done
 cmp word [es:20],0x1f65 ;e in Redisplay
 jne .done
 inc word [sample+4]
 mov bx,[sample+2]
 cmp bx,32
 jae .done
 or bx,bx
 jz .capture
 dec bx
 mov ax,320
 mul bx
 mov si,frames
 add si,ax
 mov di,160
 mov cx,240
.compare:
 mov al,[es:di]
 cmp [si],al
 jne .capture
 inc si
 add di,2
 loop .compare
 mov di,3840
 mov cx,80
.compare_footer:
 mov al,[es:di]
 cmp [si],al
 jne .capture
 inc si
 add di,2
 loop .compare_footer
 jmp .done
.capture:
 mov ax,320
 mul word [sample+2]
 mov si,frames
 add si,ax
 mov di,160
 mov cx,240
.row:
 mov al,[es:di]
 mov [si],al
 inc si
 add di,2
 loop .row
 mov di,3840
 mov cx,80
.footer:
 mov al,[es:di]
 mov [si],al
 inc si
 add di,2
 loop .footer
 inc word [sample+2]
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
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4452
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,10246
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
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,10246
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,10246
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\RVIEW.BIN',0
buffer: times 10246 db 0
