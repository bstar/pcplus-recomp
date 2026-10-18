; Independent test-only INT1C sampler. Never patches or calls product code.
; WATCH T installs; WATCH samples/unhooks and writes six words to WATCH.BIN.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
sample: dw 0x4c42,0,0,0,0,0 ; magic,total,BREAK,post-BREAK,lastLCR,video-digit mask
seen: dw 0
handler:
 pushf
 push ax
 push dx
 push ds
 push cs
 pop ds
 inc word [sample+2]
 mov dx,0x3fb
 in al,dx
 xor ah,ah
 mov [sample+8],ax
 test al,0x40
 jz .clear
 inc word [sample+4]
 mov word [seen],1
 ; Observe independently changing RX text while BREAK is asserted.
 push bx
 push cx
 push es
 mov ax,0xb800
 mov es,ax
 mov cl,[es:0]
 sub cl,'0'
 cmp cl,9
 ja .video_done
 mov ax,1
 shl ax,cl
 or [sample+10],ax
.video_done:
 pop es
 pop cx
 pop bx
 jmp .done
.clear:
 cmp word [seen],0
 je .done
 inc word [sample+6]
.done:
 pop ds
 pop dx
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
 cmp word [es:sample],0x4c42
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,6
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 popf
 ; Restore the prior INT1C before exiting this test VM.
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
 mov cx,12
 mov ah,0x40
 int 0x21
 pushf
 cmp ax,12
 jne .short
 popf
 jc .close_failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
.short:
 popf
.close_failed:
 mov ah,0x3e
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\WATCH.BIN',0
buffer: times 12 db 0
