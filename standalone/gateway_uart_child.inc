; Test-only COMSPEC prelude; child uses a foreign DS while the parent IRQ runs.
 jmp gateway_child_start
gateway_child_state: times 16 db 0
gateway_child_name: db 'D:\GUSHELL.BIN',0
gateway_child_start:
 mov dx,PORT_BASE+5
.tx:
 in al,dx
 test al,0x20
 jz .tx
 mov dx,PORT_BASE
 mov al,'D'
 out dx,al
 call .snapshot
 mov si,gateway_child_state
 mov [si],bx
 mov [si+2],cx
 mov [si+8],ax
 mov [si+10],dl
 xor ah,ah
 int 0x1a
 mov di,dx
 push ds
 mov ax,0x7777
 mov ds,ax
.wait:
 sti
 hlt
 xor ah,ah
 int 0x1a
 sub dx,di
 cmp dx,54
 jb .wait
 pop ds
 mov [si+14],dx
 call .snapshot
 mov [si+4],bx
 mov [si+6],cx
 mov [si+11],ax
 mov [si+13],dl
 mov ah,0x3c
 xor cx,cx
 mov dx,gateway_child_name
 int 0x21
 jc .fail
 mov bx,ax
 mov dx,gateway_child_state
 mov cx,16
 mov ah,0x40
 int 0x21
 jc .fail
 mov ah,0x3e
 int 0x21
 jc .fail
 jmp gateway_child_finished
.snapshot:
 push es
 xor ax,ax
 mov es,ax
 mov bx,[es:(UART_IRQ+8)*4]
 mov cx,[es:(UART_IRQ+8)*4+2]
 pop es
 mov dx,PORT_BASE+1
 in al,dx
 mov ah,al
 mov dx,PORT_BASE+3
 in al,dx
 mov dl,al
 mov dx,PORT_BASE+4
 in al,dx
 xchg al,ah ; AX = MCR:IER; DL supplied separately below.
 push ax
 mov dx,PORT_BASE+3
 in al,dx
 mov dl,al
 pop ax
 ret
.fail:
 mov ax,0x4c01
 int 0x21
gateway_child_finished:
