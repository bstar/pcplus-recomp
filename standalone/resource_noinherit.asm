; Test-only DOS child. Probe the parent's decimal handle without opening any
; files. Only DOS invalid-handle6 counts as noninheritance; EOF is not success.
BITS 16
CPU 8086
ORG 100h
 mov si,81h
 xor bx,bx
.skip:
 lodsb
 cmp al,' '
 je .skip
.digit:
 cmp al,'0'
 jb .parsed
 cmp al,'9'
 ja .parsed
 sub al,'0'
 xor ah,ah
 push ax
 mov ax,bx
 mov cx,10
 mul cx
 pop dx
 add ax,dx
 mov bx,ax
 lodsb
 jmp .digit
.parsed:
 cmp bx,5
 jb .fail
 mov cx,1
 mov dx,probe_byte
 mov ah,3fh
 int 21h
 jnc .fail
 cmp ax,6
 jne .fail
 mov ax,4c00h
 int 21h
.fail:
 mov ax,4c01h
 int 21h
probe_byte: db 0
