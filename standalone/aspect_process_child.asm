BITS 16
CPU 8086
ORG 0x100
%if CHILD_PORT=1
%define BASE 0x3f8
%define VECTOR 12
%define MASK 16
%else
%define BASE 0x2f8
%define VECTOR 11
%define MASK 8
%endif
; The tail is constructed by recovered argv/environment code, not a synthetic
; harness callback. Its first non-space byte selects this owned child behavior.
mov si,0x81
.spaces: lodsb
cmp al,' '
je .spaces
mov [command],al
; Owned full-VM child; derived from the source-owned PROGRAM diagnostic.
; Validate the current C environment actually reached the DOS child.
mov ax,[0x2c]
mov es,ax
xor di,di
.environment:
mov bx,di
mov si,expected
mov cx,14
cld
repe cmpsb
je .environment_ok
mov di,bx
.skip: cmp byte [es:di],0
je .next
inc di
jmp short .skip
.next: inc di
cmp byte [es:di],0
jne .environment
jmp failed
.environment_ok:
; The controlled DOS fixture owns descriptors5..11 (ASX plus six streams).
; Query every possible inherited nonstandard handle before opening our own.
mov bx,5
.private:
xor cx,cx
xor dx,dx
mov ax,0x4201
int 0x21
jnc private_failed
cmp ax,6
jne failed
inc bx
cmp bx,20
jb .private
; The write-only sixth stream must be flushed before the child observes it.
mov dx,slot_name
mov ax,0x3d00
int 0x21
jc failed
mov bx,ax
mov dx,slot_buffer
mov cx,8
mov ah,0x3f
int 0x21
jc failed
cmp ax,8
jne failed
mov ah,0x3e
int 0x21
push ds
pop es
mov si,slot_expected
mov di,slot_buffer
mov cx,8
repe cmpsb
jne failed
mov ax,0x40
mov es,ax
mov cx,[es:0x4a]
xor ax,ax
mov al,[es:0x84]
inc ax
mul cx
mov [cells],ax
mov ax,0xb800
cmp byte [es:0x49],7
jne .video
mov ax,0xb000
.video:
mov [video],ax
mov es,ax
cmp byte [command],'T'
je .preserved
cmp byte [command],'N'
je .preserved
cmp byte [command],'G'
je .preserved
xor di,di
mov cx,[cells]
.clear: cmp word [es:di],0x0720
jne failed
add di,2
loop .clear
jmp short .port
.preserved:
cmp word [es:0],0x1741
jne failed
.port:
mov dx,BASE+3
in al,dx
cmp al,3
jne failed
mov dx,BASE+1
in al,dx
or al,al
jnz failed
mov dx,BASE+4
in al,dx
test al,2
jnz failed
test al,1
jz failed
mov al,1
out dx,al
mov dx,BASE+3
mov al,0x9e
out dx,al
mov dx,BASE
mov al,0x34
out dx,al
inc dx
mov al,0x12
out dx,al
in al,0x21
xor al,0x20
or al,MASK
out 0x21,al
mov ax,0x2500+VECTOR
mov dx,handler
int 0x21
cmp byte [command],'T'
je .text
cmp byte [command],'N'
je .text
cmp byte [command],'W'
je .wait_text
mov ax,0x13
int 0x10
jmp short .record
.wait_text:
mov ax,[video]
mov es,ax
xor di,di
mov ax,0x1f58
mov cx,[cells]
cld
rep stosw
jmp short .record
.text:
mov word [es:0],0x2e4e
.record:
; WAIT's real BIOS consumer must receive a key after this child returns.
cmp byte [command],'W'
jne .no_key
mov cx,0x1177
mov ah,5
int 0x16
.no_key:
mov dx,name
xor cx,cx
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,message
mov cx,5
mov ah,0x40
int 0x21
mov ah,0x3e
int 0x21
mov ax,0x4c25
cmp byte [command],'T'
jne .exit
mov ax,0x4cf7
.exit:
int 0x21
failed:
mov ax,0x4c63
int 0x21
private_failed:
mov ax,0x4c62
int 0x21
handler: iret
name: db 'CHILD.OUT',0
message: db 'COM','0'+CHILD_PORT
command: db 0
expected: db 'CTRLVAR=OWNED',0
cells: dw 0
video: dw 0

slot_name: db "SLOT5.BIN",0
slot_expected: db "pending5"
slot_buffer: times 8 db 0
