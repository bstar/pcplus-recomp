; Independent test-only INT16 observer. Chain actual BIOS reads; never supply a
; key or inspect product memory. Record selected keys with rows2/23 and ticks.
; Peek/other functions chain untouched. Read-result registers and status flags
; survive; original caller IF/TF/DF/control bits are preserved in its INT frame.
BITS 16
CPU 8086
ORG 0x100
jmp start
old_vector: dw 0,0
sample: dw 0x4b57,0,0
records: times 32*164 db 0
handler:
 cmp ah,0
 je .read
 cmp ah,0x10
 je .read
 jmp far [cs:old_vector]
.read:
 push bp
 mov bp,sp
 push ax
 mov ax,[ss:bp+6]
 and ax,0xfcff ; INT clears IF/TF; retain the original arithmetic status.
 push ax
 popf
 pop ax
 pushf
 call far [cs:old_vector]
 push ax
 push dx
 pushf
 pop dx
 mov ax,[ss:bp+6]
 and dx,0x08d5
 and ax,0xf72a
 or ax,dx
 mov [ss:bp+6],ax
 pop dx
 pop ax
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
 cmp ax,0x8300
 je .record
 cmp ax,0x8400
 je .record
 cmp ax,0x84e0
 je .record
 cmp ax,0x1300
 je .record
 cmp al,27
 je .record
 cmp al,'p'
 je .record
 cmp al,'s'
 je .record
 cmp al,'t'
 jne .done
.record:
 mov di,ax
 mov bx,[sample+2]
 cmp bx,32
 jb .space
 inc word [sample+4]
 jmp .done
.space:
 mov ax,164
 mul bx
 mov si,records
 add si,ax
 mov [si],di
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov [si+2],ax
 add si,4
 mov ax,0xb800
 mov es,ax
 mov di,320
 mov cx,80
 cld
.header:
 mov al,[es:di]
 mov [si],al
 inc si
 add di,2
 loop .header
 mov di,3680
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
 pop bp
 iret
resident_end:
start:
 mov ax,0x3516
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x2516
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4b57
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,5254
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov bx,[es:old_vector]
 mov [restore_offset],bx
 mov dx,bx
 mov ax,[es:old_vector+2]
 mov [restore_segment],ax
 popf
 push ds
 mov ds,ax
 mov ax,0x2516
 int 0x21
 pop ds
 mov ax,0x3516
 int 0x21
 cmp bx,[restore_offset]
 jne failed
 mov ax,es
 cmp ax,[restore_segment]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,5254
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,5254
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
restore_offset: dw 0
restore_segment: dw 0
filename: db 'D:\KWATCH.BIN',0
buffer: times 5254 db 0
