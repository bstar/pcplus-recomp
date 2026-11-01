; Passive BIOS-timer speaker/video observer. Never writes PIT/speaker ports.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
stats:
 dw 0xca17
samples: dw 0
high_ticks: dw 0
edges: dw 0
banner_high: dw 0
final_gate: dw 0
last_gate: db 0
banner: db 'FIRST BYTE SAFE'
handler:
 pushf
 push ax
 push cx
 push si
 push di
 push ds
 push es
 inc word [cs:samples]
 in al,0x61
 and al,3
 cmp al,3
 jne .remember
 inc word [cs:high_ticks]
 cmp byte [cs:last_gate],3
 je .video
 inc word [cs:edges]
.video:
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov si,banner
 mov cx,14
.match:
 mov al,[cs:si]
 cmp al,[es:di]
 jne .sample_gate
 inc si
 add di,2
 loop .match
 inc word [cs:banner_high]
.sample_gate:
 mov al,3
.remember:
 mov [cs:last_gate],al
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
 cmp word [es:stats],0xca17
 jne failed
 in al,0x61
 and ax,3
 mov [es:final_gate],ax
 push es
 push ds
 mov dx,[es:old_vector]
 mov ax,[es:old_vector+2]
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 pop es
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 push ds
 mov ax,es
 mov ds,ax
 mov dx,stats
 mov cx,12
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,12
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'TONE.BIN',0
