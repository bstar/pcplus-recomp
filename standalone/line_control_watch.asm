; Passive timer witness: owned LC-A..LC-E markers at row0,column69.
; Read actual BDA geometry and bottomtwo physical rows. No product writes/IO.
BITS 16
CPU 8086
ORG 100h
%ifndef EXPECTED_MASK
%error Expected stage mask is required
%endif
jmp start
old_vector: dw 0,0
sample: dw 0x4c43,1
mask: dw 0
records: times 5*334 db 0
sample_end:
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
 cld
 mov ax,0x40
 mov es,ax
 cmp word [es:0x4a],80
 jne .done
 cmp byte [es:0x62],0
 jne .done
 mov al,[es:0x49]
 cmp al,2
 je .mode
 cmp al,3
 jne .done
.mode:
 mov al,[es:0x84]
 cmp al,24
 je .rows
 cmp al,27
 je .rows
 cmp al,42
 je .rows
 cmp al,49
 jne .done
.rows:
 mov ax,0xb800
 mov es,ax
 cmp byte [es:138],'L'
 jne .done
 cmp byte [es:140],'C'
 jne .done
 cmp byte [es:142],'-'
 jne .done
 xor ax,ax
 mov al,[es:144]
 sub al,'A'
 cmp al,4
 ja .done
 mov bx,ax
 mov cl,al
 mov ax,1
 shl ax,cl
 test [cs:mask],ax
 jnz .done
 or [cs:mask],ax
 mov ax,bx
 mov cx,334
 mul cx
 add ax,records
 mov di,ax
 push cs
 pop es
 mov ax,0x40
 mov ds,ax
 xor ax,ax
 mov al,[0x84]
 inc ax
 stosw
 mov ax,[0x85]
 stosw
 mov ax,[0x50]
 stosw
 mov ax,[0x60]
 stosw
 xor ax,ax
 mov al,[0x49]
 stosw
 mov ax,[0x4a]
 stosw
 xor ax,ax
 mov al,[0x62]
 stosw
 xor ax,ax
 mov al,[0x84]
 dec ax
 mov cx,160
 mul cx
 mov si,ax
 mov ax,0xb800
 mov ds,ax
 mov cx,160
 rep movsw
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
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4c43
 jne failed
 mov ax,[es:old_vector+2]
 mov dx,[es:old_vector]
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
 push ds
 push es
 pop ds
 mov dx,sample
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,sample_end-sample
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 cmp word [es:mask],EXPECTED_MASK
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\LINES.BIN',0
