; Test-only PROGRAM child. Read the retained parent context without modifying
; it, allocate/fill a separate DOS block, then compare all496 bytes exactly.
BITS 16
CPU 8086
ORG 0x100
start:
 mov ax,cs
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov ds,ax
 mov es,ax
 mov bx,(stack_top-$$+0x100+15)/16
 mov ah,0x4a
 int 0x21
 jc save
 mov bx,[0x16]
 mov cx,8
.find:
 cmp bx,0x10
 jb save
 mov ax,bx
 add ax,16+DGROUP_SEG
 mov es,ax
 cmp [es:PROCESS_PSP],bx
 jne .next
 cmp word [es:CONTEXT_VALID],1
 jne .next
 cmp word [es:CONTEXT],17
 jne .next
 or word [result+2],1
 mov [result+4],bx
 mov [result+6],ax
 dec bx
 mov es,bx
 mov ax,[es:3]
 mov [result+8],ax
 cmp ax,REQUIRED_PARAS
 jb save
 or word [result+2],2
 mov es,[result+6]
 mov si,CONTEXT
 mov di,snapshot
 mov cx,496
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov bx,0x400
 mov ah,0x48
 int 0x21
 jc save
 mov [result+10],ax
 mov dx,[result+4]
 cmp ax,dx
 jb .below
 add dx,[result+8]
 cmp ax,dx
 jb .free
 jmp .fill
.below:
 add ax,0x400
 cmp ax,dx
 ja .free
.fill:
 mov es,[result+10]
 xor di,di
 mov ax,0x5a5a
 mov cx,8192
 cld
 rep stosw
 or word [result+2],4
 mov es,[result+6]
 mov di,CONTEXT
 mov si,snapshot
 mov cx,496
 repe cmpsb
 jne .free
 or word [result+2],8
.free:
 mov es,[result+10]
 mov ah,0x49
 int 0x21
 jmp save
.next:
 mov es,bx
 mov bx,[es:0x16]
 dec cx
 jz save
 jmp .find
save:
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,result
 mov cx,508
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,508
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
filename: db 'D:\CONTEXT.BIN',0
result: dw 0x4358,0,0,0,0,0
snapshot: times 496 db 0
times 1024 db 0
stack_top:
