; Read-only observations; owns only its TSR counters and output file.
BITS 16
CPU 8086
ORG 100h
jmp start
old21: dw 0,0
old1c: dw 0,0
sample:
magic: dw 0x434d
parent_ds: dw 0
ticks: dw 0
initializing_paused: dw 0
first_DCD_high: dw 0
first_seen_high: dw 0
first_DTR_low: dw 0
cancel_seen: dw 0
cancel_pause: dw 0xffff
cancel_seen_high: dw 0xffff
online_ticks: dw 0
done: dw 0
sample_end:
%macro save 0
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
%endmacro
%macro restore 0
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
%endmacro
hook21:
 save
 cmp ah,0x3d
 jne .exit
 mov bx,ds
 mov cx,ss
 cmp bx,cx
 jne .chain
 mov si,dx
 mov di,prm_name
 mov cx,12
.name:
 mov al,[si]
 cmp al,[cs:di]
 jne .chain
 inc si
 inc di
 loop .name
 cmp word [cs:parent_ds],0
 jne .chain
 mov [cs:parent_ds],bx
 jmp .chain
.exit:
 cmp ah,0x4c
 jne .chain
 mov bx,ds
 cmp bx,[cs:parent_ds]
 jne .chain
 mov word [cs:done],1
.chain:
 restore
 jmp far [cs:old21]
timer:
 save
 cld
 cmp word [cs:done],0
 jne .end
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .end
 mov dx,ss
 cmp ax,dx
 jne .end
 mov es,ax
 inc word [cs:ticks]
 cmp word [cs:cancel_seen],0
 jne .online
 mov dx,0x3fe
 in al,dx
 test al,0x80
 jz .carrier
 inc word [cs:first_DCD_high]
.carrier:
 cmp byte [es:CARRIER_SEEN],0
 je .state
 inc word [cs:first_seen_high]
.state:
 cmp word [es:STATE],1
 jne .DTR
 cmp word [es:PAUSED],1
 jne .DTR
 inc word [cs:initializing_paused]
.DTR:
 cmp word [cs:initializing_paused],0
 je .idle
 mov dx,0x3fc
 in al,dx
 test al,1
 jnz .idle
 inc word [cs:first_DTR_low]
.idle:
 cmp word [es:STATE],0
 jne .end
 cmp word [es:STATUS],4
 jne .end
 mov word [cs:cancel_seen],1
 mov ax,[es:PAUSED]
 mov [cs:cancel_pause],ax
 xor ax,ax
 mov al,[es:CARRIER_SEEN]
 mov [cs:cancel_seen_high],ax
 jmp .end
.online:
 cmp word [es:STATE],6
 jne .end
 inc word [cs:online_ticks]
.end:
 restore
 jmp far [cs:old1c]
prm_name: db 'D:\TEST.PRM',0
resident_end:
start:
 push cs
 pop ds
 mov ax,0x351c
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old1c],bx
 mov [old1c+2],es
 mov ax,0x3521
 int 0x21
 mov [old21],bx
 mov [old21+2],es
 mov dx,hook21
 mov ax,0x2521
 int 0x21
 mov dx,timer
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,timer
 jne failed
 cmp word [es:magic],0x434d
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,sample_end-sample
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 push ds
 mov dx,[es:old21]
 mov ax,[es:old21+2]
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 push ds
 mov dx,[es:old1c]
 mov ax,[es:old1c+2]
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
 mov cx,sample_end-sample
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,sample_end-sample
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\CANCEL.BIN',0
buffer: times sample_end-sample db 0
