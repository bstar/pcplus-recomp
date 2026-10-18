; Independent setup test INT1C UART-divisor sampler; never calls product code.
; Temporarily selects DLL/DLH only with interrupts masked, then restores LCR.
; WATCH T installs; WATCH unhooks and writes six words to WATCH.BIN.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
sample: dw 0x5355,0,0,0,0,0 ; magic,total,divisor-bitmask,last-divisor,active-ticks,reserved
handler:
 pushf
 cli
 push ax
 push bx
 push dx
 push ds
 push cs
 pop ds
 inc word [sample+2]
 mov dx,0x3fb
 in al,dx
 mov bl,al
 test al,0x80
 jnz .done
 mov dx,0x3f9
 in al,dx
 test al,1
 jz .done
 inc word [sample+8]
 mov dx,0x3fb
 mov al,bl
 or al,0x80
 out dx,al
 mov dx,0x3f8
 in al,dx
 mov ah,al
 inc dx
 in al,dx
 xchg al,ah
 push ax
 mov dx,0x3fb
 mov al,bl
 out dx,al
 pop ax
 mov [sample+6],ax
 cmp ax,96
 jne .baud115200
 or word [sample+4],1
 jmp .done
.baud115200:
 cmp ax,1
 jne .baud19200
 or word [sample+4],2
 jmp .done
.baud19200:
 cmp ax,6
 jne .done
 or word [sample+4],4
.done:
 pop ds
 pop dx
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
 cmp word [es:sample],0x5355
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
