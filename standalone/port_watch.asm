; Independent multiport INT1C sampler for live COM selection tests.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
sample: dw 0x5043,0
 times 16 dw 0 ; per port: active ticks, divisor bitmap, last divisor, LCR bitmap
bases: dw 0x3f8,0x2f8,0x3e8,0x2e8
handler:
 pushf
 cli
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push cs
 pop ds
 inc word [sample+2]
 xor si,si
 mov di,sample+4
 mov cx,4
.port:
 mov bp,[bases+si]
 mov dx,bp
 add dx,3
 in al,dx
 mov bl,al
 test al,0x80
 jnz .next
 mov dx,bp
 inc dx
 in al,dx
 test al,1
 jz .next
 inc word [di]
 cmp bl,3
 jne .format7e2
 or word [di+6],1
 jmp .divisor
.format7e2:
 cmp bl,0x1e
 jne .other
 or word [di+6],2
 jmp .divisor
.other:
 or word [di+6],4
.divisor:
 mov dx,bp
 add dx,3
 mov al,bl
 or al,0x80
 out dx,al
 mov dx,bp
 in al,dx
 mov ah,al
 inc dx
 in al,dx
 xchg al,ah
 push ax
 mov dx,bp
 add dx,3
 mov al,bl
 out dx,al
 pop ax
 mov [di+4],ax
 cmp ax,96
 jne .baud115200
 or word [di+2],1
 jmp .next
.baud115200:
 cmp ax,1
 jne .baud19200
 or word [di+2],2
 jmp .next
.baud19200:
 cmp ax,6
 jne .next
 or word [di+2],4
.next:
 add si,2
 add di,8
 loop .port
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
 ; Ensure the installed sampler has actually ticked, even for a fast failed
 ; EXEC. This establishes a live timer, not continuous observation of every IO.
.wait_tick:
 cmp word [sample+2],0
 je .wait_tick
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x5043
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,18
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
 mov cx,36
 mov ah,0x40
 int 0x21
 pushf
 cmp ax,36
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
buffer: times 36 db 0
