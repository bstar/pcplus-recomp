; Source-owned DOS COM child. Writes only named synthetic diagnostic artifacts.
BITS 16
CPU 8086
ORG 0x100
start:
 push cs
 pop ds
 cld
 mov dx,tail_name
 call create
 mov dx,0x80
 xor cx,cx
 mov cl,[0x80]
 add cx,2
 call write_close
 mov dx,fcb_name
 call create
 mov dx,0x5c
 mov cx,32
 call write_close
 mov es,[0x2c]
 xor bx,bx
.environment:
 mov di,bx
 cmp byte [es:di],0
 je error
 mov si,environment_name
 mov cx,17
 repe cmpsb
 je .found
.skip:
 cmp byte [es:bx],0
 je .next
 inc bx
 jnz .skip
 jmp error
.next:
 inc bx
 jnz .environment
 jmp error
.found:
 mov si,di
 xor cx,cx
.value:
 cmp byte [es:di],0
 je .copy
 cmp cx,127
 jae error
 inc di
 inc cx
 jmp .value
.copy:
 mov [value_length],cx
 mov di,environment_value
.byte:
 jcxz .save
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .byte
.save:
 mov dx,environment_file
 call create
 mov dx,environment_value
 mov cx,[value_length]
 call write_close
 ; Clobber ordinary child registers before DOS returns the parent's context.
 mov bp,0x1234
 mov si,0x5678
 mov di,0xabcd
 mov ax,0x4c25
 int 0x21
create:
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc error
 mov bx,ax
 ret
write_close:
 mov ah,0x40
 int 0x21
 jc error
 cmp ax,cx
 jne error
 mov ah,0x3e
 int 0x21
 jc error
 ret
error:
 mov ax,0x4cff
 int 0x21
tail_name: db 'CHILD.OUT',0
fcb_name: db 'FCBS.OUT',0
environment_file: db 'ENV.OUT',0
environment_name: db 'PCPLUS_EXEC_TEST='
value_length: dw 0
environment_value: times 128 db 0
