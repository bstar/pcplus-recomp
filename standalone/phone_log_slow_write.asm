; Owned DOS fixture: delay first real log data write with IRQs enabled.
; Reads parent UART counters through its actual DS; never writes product state.
BITS 16
CPU 8086
ORG 100h
%ifndef DELAY_TICKS
%define DELAY_TICKS 9
%endif
jmp start
old_dos: dd 0
sample: dw 0x534c,0,DELAY_TICKS,0,0,0,0,0,0,0,0,0,0xffff,0,0,0
%define FIRED (sample+2)
%define ELAPSED (sample+6)
%define ENTRY_FLAGS (sample+8)
%define ACTIVE (sample+10)
%define RX_BEFORE (sample+12)
%define RX_PEAK (sample+14)
%define DROP_BEFORE (sample+16)
%define DROP_AFTER (sample+18)
%define REAL_AX (sample+20)
%define REAL_FLAGS (sample+22)
%define HELD (sample+24)
%define MCR (sample+26)
%define WAIT_FLAGS (sample+28)
%define PARENT_DS (sample+30)
path: db 'D:\PCPLUS.FON',0
handler:
 pushf
 push bp
 mov bp,sp
 cmp word [cs:FIRED],0
 jne .pass
 cmp ah,3ch
 je .open
 cmp ah,3dh
 je .open
 cmp ah,5bh
 je .open
 cmp ah,40h
 jne .pass
 cmp bx,[cs:HELD]
 jne .pass
 or cx,cx
 jz .pass
 mov word [cs:FIRED],1
 mov ax,[ss:bp+8]
 mov [cs:ENTRY_FLAGS],ax
 call hold
 ; Restore the genuine data-write function; AX was used to read FLAGS.
 mov ah,40h
 pushf
 call far [cs:old_dos]
 mov [cs:REAL_AX],ax
 pushf
 pop word [cs:REAL_FLAGS]
 jc .error
 and word [ss:bp+8],0xfffe
 jmp .return
.open:
 call matches
 jnc .pass
 pushf
 call far [cs:old_dos]
 jc .error
 mov [cs:HELD],ax
 and word [ss:bp+8],0xfffe
 jmp .return
.error:
 or word [ss:bp+8],1
.return:
 pop bp
 popf
 iret
.pass:
 pop bp
 popf
 jmp far [cs:old_dos]
hold:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push es
 mov ax,ds
 mov [cs:PARENT_DS],ax
 xor ax,ax
 mov al,[HARDWARE_ACTIVE_OFFSET]
 mov [cs:ACTIVE],ax
 mov ax,[RX_COUNT_OFFSET]
 mov [cs:RX_BEFORE],ax
 mov [cs:RX_PEAK],ax
 mov ax,[RX_DROPPED_OFFSET]
 mov [cs:DROP_BEFORE],ax
 mov dx,3fch
 in al,dx
 xor ah,ah
 mov [cs:MCR],ax
 test word [cs:ENTRY_FLAGS],200h
 jz .done
 mov ax,40h
 mov es,ax
 mov si,[es:6ch]
 mov cx,0xffff
 mov bx,64
 sti
.loop:
 mov ax,[RX_COUNT_OFFSET]
 cmp ax,[cs:RX_PEAK]
 jbe .tick
 mov [cs:RX_PEAK],ax
.tick:
 pushf
 pop ax
 mov [cs:WAIT_FLAGS],ax
 mov ax,[es:6ch]
 sub ax,si
 cmp ax,DELAY_TICKS
 jae .elapsed
 loop .loop
 dec bx
 jz .elapsed
 mov cx,0xffff
 jmp .loop
.elapsed:
 mov [cs:ELAPSED],ax
 cli
.done:
 mov ax,[RX_DROPPED_OFFSET]
 mov [cs:DROP_AFTER],ax
 pop es
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
matches:
 push ax
 push bx
 push cx
 push si
 mov si,dx
 add si,14
 jc .missing
 mov si,dx
 mov bx,path
 mov cx,14
.loop:
 mov al,[si]
 cmp al,[cs:bx]
 jne .missing
 inc si
 inc bx
 loop .loop
 pop si
 pop cx
 pop bx
 pop ax
 stc
 ret
.missing:
 pop si
 pop cx
 pop bx
 pop ax
 clc
 ret
resident_end:
start:
 mov ax,3521h
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_dos],bx
 mov [old_dos+2],es
 mov dx,handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x534c
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,32
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 mov [old_dos],dx
 mov [old_dos+2],ax
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[old_dos]
 jne failed
 mov ax,es
 cmp ax,[old_dos+2]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,32
 mov ah,40h
 int 21h
 jc .close_failed
 cmp ax,32
 jne .close_failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
.close_failed:
 mov ah,3eh
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\SLOW.BIN',0
buffer: times 32 db 0
