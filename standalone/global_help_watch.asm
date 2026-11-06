; Passive INT1C observer: reference -> Help -> same reference. No product
; addresses, injected keys, DOS calls in ISR or writes to product/video state.
BITS 16
CPU 8086
ORG 100h
jmp start
old: dd 0
sample: dw 0x4847,0,0,0,0,0,0,0,0,0
frames: times 24000 db 0xa5
last: dw 0
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
%ifdef WATCH_REPEAT
 cmp word [sample+2],5
%else
 cmp word [sample+2],3
%endif
 jae .done
 mov ax,0xb800
 mov es,ax
 cmp word [sample+2],1
 je .help
%ifdef WATCH_REPEAT
 cmp word [sample+2],3
 je .help
%endif
 cmp byte [es:190],'P'
 jne .done
 cmp byte [es:194],'R'
 jne .done
 cmp byte [es:198],'O'
 jne .done
 jmp .candidate
.help:
%ifdef WATCH_FAILURE
 cmp byte [es:160],'P'
 jne .done
 cmp byte [es:162],'r'
 jne .done
 cmp byte [es:164],'o'
 jne .done
%else
 cmp byte [es:2],'T'
 jne .done
 cmp byte [es:4],'e'
 jne .done
 cmp byte [es:6],'r'
 jne .done
%endif
.candidate:
 push es
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 pop es
 cmp ax,50
 ja .done
 mov [sample+6],ax
 mov bx,80
 mul bx
 mov cx,ax
 xor si,si
 xor dx,dx
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
 mov bx,[sample+2]
%ifdef WATCH_REPEAT
 cmp bx,3
 jb .metadata_index
 sub bx,2
.metadata_index:
%endif
 shl bx,1
 shl bx,1
 push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [sample+8+bx],ax
 mov ax,[es:0x60]
 mov [sample+10+bx],ax
 pop es
 mov ax,[sample+2]
%ifdef WATCH_REPEAT
 cmp ax,3
 jb .frame_index
 sub ax,2
.frame_index:
%endif
 mov bx,8000
 mul bx
 mov di,frames
 add di,ax
 mov ax,[sample+6]
 mov bx,80
 mul bx
 mov cx,ax
 xor si,si
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 inc word [sample+2]
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
 mov ax,0x351c
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4847
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,24020
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old]
 mov ax,[es:old+2]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 popf
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,24020
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,24020
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
name: db 'HELPUI.BIN',0
buffer: resb 24020
