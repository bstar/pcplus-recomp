; Independent INT1C text-video observer. Capture the real splash before a key.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
observed: dw 0
ticks: dw 0
edition: db 'LoC SPECIAL EDITION'
screen: times 4000 db 0
later: times 4000 db 0
handler:
 pushf
 push ax
 push cx
 push si
 push di
 push ds
 push es
 inc word [cs:ticks]
 cmp word [cs:ticks],80
 jne .splash
 cld
 mov ax,0xb800
 mov ds,ax
 push cs
 pop es
 xor si,si
 mov di,later
 mov cx,2000
 rep movsw
.splash:
 cmp word [cs:observed],0
 jne .done
 mov ax,0xb800
 mov es,ax
 mov di,(9*80+27)*2
 mov si,edition
 mov cx,19
.match:
 mov al,[cs:si]
 cmp al,[es:di]
 jne .done
 inc si
 add di,2
 loop .match
 cld
 mov ax,0xb800
 mov ds,ax
 push cs
 pop es
 xor si,si
 mov di,screen
 mov cx,2000
 rep movsw
 mov word [cs:observed],1
.done:
 pop es
 pop ds
 pop di
 pop si
 pop cx
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
 cmp word [es:observed],1
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
 mov dx,screen
 mov cx,8000
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,8000
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'C:\SPLASH.BIN',0
