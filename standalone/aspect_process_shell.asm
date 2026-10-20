; Owned COMSPEC wrapper: enter a real DOS command processor, feed EXIT through
; its BIOS keyboard, then record normal nested EXEC return. Not a shell stub.
BITS 16
CPU 8086
ORG 0x100
cli
mov ax,cs
mov ss,ax
mov sp,0x7fe
sti
mov ds,ax
mov es,ax
mov bx,0x80
mov ah,0x4a
int 0x21
jc failed
mov si,keys
.key:
lodsb
or al,al
jz .execute
mov cl,al
xor ch,ch
mov ah,5
int 0x16
or al,al
jnz failed
jmp short .key
.execute:
mov ax,cs
mov [tail_segment],ax
mov [first_segment],ax
mov [second_segment],ax
mov dx,shell
mov bx,parameters
mov ax,0x4b00
int 0x21
push cs
pop ds
jc failed
mov ah,0x4d
int 0x21
or ax,ax
jnz failed
mov dx,marker
xor cx,cx
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,message
mov cx,9
mov ah,0x40
int 0x21
mov ah,0x3e
int 0x21
mov ax,0x4c00
int 0x21
failed: mov ax,0x4c63
int 0x21
keys: db 'exit',13,0
shell: db 'Z:\COMMAND.COM',0
marker: db 'SHELL.OUT',0
message: db 'SHELLREAL',13
tail: db 0,13
parameters: dw 0,tail
tail_segment: dw 0
dw 0x5c
first_segment: dw 0
dw 0x6c
second_segment: dw 0
