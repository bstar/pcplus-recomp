; Test-only INT16 observer. Actual BIOS reads only; no supplied keys or product
; writes/callbacks. Unlike behavioral observers, this diagnostic deliberately
; reads map-bound application guard words through the interrupted caller's DS.
BITS 16
CPU 8086
ORG 0x100
%include "menu-guards.inc"
%define RECORD_BYTES (16+2*GUARD_COUNT+8+240)
%define SAMPLE_BYTES (12+32*RECORD_BYTES)
jmp start
old_vector: dw 0,0
armed: dw 0
sample: dw 0x474d,1,RECORD_BYTES,GUARD_COUNT,0,0
records: times 32*RECORD_BYTES db 0
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
 and ax,0xfcff
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
 cmp ax,0x2c00
 jne .already
 mov word [armed],1
.already:
 cmp word [armed],0
 je .done
 cmp ax,0x2c00
 je .record
 cmp ax,0x4d00
 je .record
 cmp ax,0x4de0
 je .record
 cmp ax,0x8300
 je .record
 cmp al,'f'
 je .record
 cmp al,'a'
 je .record
 cmp al,'s'
 je .record
 cmp al,13
 je .record
 cmp al,27
 jne .done
.record:
 mov di,ax
 mov bx,[sample+8]
 cmp bx,32
 jb .space
 inc word [sample+10]
 jmp .done
.space:
 mov ax,RECORD_BYTES
 mul bx
 mov si,records
 add si,ax
 mov [si],di
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov [si+2],ax
 mov ax,[es:0x6e]
 mov [si+4],ax
 mov ax,[ss:bp+2]
 mov [si+6],ax
 mov ax,[ss:bp+4]
 mov [si+8],ax
 mov ax,[ss:bp-14] ; actual DS saved after the BIOS returned
 mov [si+10],ax
 mov es,ax
 mov ax,ss
 mov [si+12],ax
 mov [si+14],bp
 add si,16
 mov di,guard_offsets
 mov cx,GUARD_COUNT
.guards:
 mov bx,[di]
 mov ax,[es:bx]
 mov [si],ax
 add si,2
 add di,2
 loop .guards
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x49]
 mov [si],ax
 mov ax,[es:0x4a]
 mov [si+2],ax
 xor ax,ax
 mov al,[es:0x62]
 mov [si+4],ax
 mov al,[es:0x84]
 mov [si+6],ax
 add si,8
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,80
.title:
 mov al,[es:di]
 mov [si],al
 inc si
 add di,2
 loop .title
 mov di,320
 mov cx,80
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
 inc word [sample+8]
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
guard_offsets: GUARD_OFFSETS
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
 cmp word [es:sample],0x474d
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,SAMPLE_BYTES
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
 mov cx,SAMPLE_BYTES
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,SAMPLE_BYTES
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
filename: db 'D:\MGUARD.BIN',0
buffer: times SAMPLE_BYTES db 0
