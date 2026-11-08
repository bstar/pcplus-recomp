; Experimental far DOS boundary. No CRT, borrowed DS, or near parent pointers.
BITS 16
CPU 8086
SEGMENT LEASE_IO_CODE public align=16 class=FARCODE use16
%macro entry 1
 global _lease_dos_%1
_lease_dos_%1:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
%endmacro
%macro leave 0
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endmacro
entry context
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 test ax,0x0400
 jnz .bad
 test ax,0x0200
 jz .bad
 mov ax,1
 jmp .done
.bad: xor ax,ax
.done: leave
entry psp
 mov ah,0x51
 int 0x21
 mov ax,bx
 leave
entry version
 mov ah,0x30
 int 0x21
 xor ah,ah
 leave
entry drive
 mov ah,0x19
 int 0x21
 xor ah,ah
 leave
entry error
 mov ax,[cs:last_error]
 leave
entry cwd
 lds si,[ss:bp+6]
 xor dl,dl
 mov ah,0x47
 int 0x21
 jmp status
entry create
 lds si,[ss:bp+6]
 mov ax,0x6c00
 mov bx,0x0092 ; read/write, deny both, no inheritance
 xor cx,cx
 mov dx,0x0010 ; fail if exists; create if absent
 int 0x21
 jmp value
entry exists
 lds dx,[ss:bp+6]
 mov ax,0x4300
 int 0x21
 jnc .yes
 cmp ax,2
 je .no
 cmp ax,3
 jne error_value
.no:
 xor ax,ax
 jmp .done
.yes:
 mov ax,1
.done:
 mov word [cs:last_error],0
 leave
entry open
 lds dx,[ss:bp+6]
 mov ax,0x3d90 ; read-only, deny both, no inheritance
 int 0x21
 jmp value
entry unlink
 lds dx,[ss:bp+6]
 mov ah,0x41
 int 0x21
 jmp status
entry close
 mov bx,[ss:bp+6]
 mov ah,0x3e
 int 0x21
 jmp status
entry rewind
 mov bx,[ss:bp+6]
 xor cx,cx
 xor dx,dx
 mov ax,0x4200
 int 0x21
 jmp status
entry resize
 ; SETBLOCK can assign the resized arena to CurrentPDB (MS-DOS4 ALLOC).
 ; Scope ONLY this operation to its checked owner, then restore the caller
 ; on both success and failure. File handles remain owned by the child.
 mov ah,0x51
 int 0x21
 push bx
 mov bx,[ss:bp+6]
 mov ah,0x50
 int 0x21
 mov es,[ss:bp+6]
 mov bx,[ss:bp+8]
 mov ah,0x4a
 int 0x21
 pushf
 push ax
 mov bx,[ss:bp-16]
 mov ah,0x50
 int 0x21
 pop ax
 popf
 pop bx
 jmp status
entry read
 mov bx,[ss:bp+6]
 lds dx,[ss:bp+8]
 mov cx,[ss:bp+12]
 mov ah,0x3f
 int 0x21
 jmp value
entry write
 mov bx,[ss:bp+6]
 lds dx,[ss:bp+8]
 mov cx,[ss:bp+12]
 mov ah,0x40
 int 0x21
 jmp value
status:
 jc error_status
 mov word [cs:last_error],0
 xor ax,ax
 leave
value:
 jc error_value
 mov word [cs:last_error],0
 leave
error_status:
 mov [cs:last_error],ax
 leave
error_value:
 mov [cs:last_error],ax
 mov ax,0xffff
 leave
last_error: dw 0
SEGMENT LEASE_STORAGE public align=16 class=FAR_DATA use16
global _compiler_lease_storage
_compiler_lease_storage: dw 0
 resb 4350
