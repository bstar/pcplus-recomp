; Owned test TSR: after explicit child arming, fail the selected KBD close.
; The real DOS close runs first. No application memory or file bytes change.
BITS 16
CPU 8086
ORG 100h
jmp start
old21: dd 0
old2f: dd 0
report: dw 4b46h,0,0,0,0,0
tracked: dw 0ffffh
path: db 'D:\SYN.KBD',0
hook2f:
 cmp ax,0d74ah
 jne .chain
 or bx,bx
 jz .query
 cmp bx,1
 jne .chain
 mov word [cs:report+2],1
.query:
 mov ax,4b46h
 push cs
 pop es
 mov di,report
 iret
.chain:
 jmp far [cs:old2f]
match:
 push ax
 push cx
 push si
 push di
 mov si,dx
 mov di,path
 mov cx,11
.loop:
 mov al,[si]
 cmp al,[cs:di]
 jne .no
 inc si
 inc di
 loop .loop
 stc
 jmp .done
.no:
 clc
.done:
 pop di
 pop si
 pop cx
 pop ax
 ret
hook21:
 cmp word [cs:report+2],1
 jne .chain
 cmp ah,3dh
 je .open
 cmp ah,3eh
 jne .chain
 cmp bx,[cs:tracked]
 jne .chain
 pushf
 call far [cs:old21]
 jc .real_failed
 mov word [cs:tracked],0ffffh
 mov word [cs:report+2],0
 inc word [cs:report+6]
 mov word [cs:report+10],1
 mov ax,6
 stc
 jmp status_return
.real_failed:
 mov [cs:report+8],ax
 jmp status_return
.open:
 call match
 jnc .chain
 pushf
 call far [cs:old21]
 jc status_return
 mov [cs:tracked],ax
 inc word [cs:report+4]
 clc
 jmp status_return
.chain:
 jmp far [cs:old21]
status_return:
 ; Preserve the interrupted caller's IF and all flags except DOS carry.
 push bp
 mov bp,sp
 push ax
 pushf
 pop ax
 and ax,1
 and word [ss:bp+6],0fffeh
 or [ss:bp+6],ax
 pop ax
 pop bp
 iret
resident_end:
local: times 20 db 0
name: db 'D:\KBCLOSE.BIN',0
start:
 cmp byte [82h],'T'
 je install
 mov ax,0d74ah
 xor bx,bx
 int 2fh
 cmp ax,4b46h
 jne failed
 ; Copy the resident report and old vectors into this transient invocation.
 push ds
 mov ax,es
 mov ds,ax
 push cs
 pop es
 mov si,report
 mov di,local
 mov cx,6
 cld
 rep movsw
 mov si,old21
 mov cx,4
 rep movsw
 pop ds
 push ds
 mov dx,[local+12]
 mov ds,[local+14]
 mov ax,2521h
 int 21h
 pop ds
 push ds
 mov dx,[local+16]
 mov ds,[local+18]
 mov ax,252fh
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[local+12]
 jne failed
 mov ax,es
 cmp ax,[local+14]
 jne failed
 mov ax,352fh
 int 21h
 cmp bx,[local+16]
 jne failed
 mov ax,es
 cmp ax,[local+18]
 jne failed
 mov word [local+12],1
 mov dx,name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,local
 mov cx,14
 mov ah,40h
 int 21h
 jc failed
 cmp ax,14
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
install:
 mov ax,3521h
 int 21h
 mov [old21],bx
 mov [old21+2],es
 mov ax,352fh
 int 21h
 mov [old2f],bx
 mov [old2f+2],es
 mov dx,hook21
 mov ax,2521h
 int 21h
 mov dx,hook2f
 mov ax,252fh
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
failed:
 mov ax,4c01h
 int 21h
