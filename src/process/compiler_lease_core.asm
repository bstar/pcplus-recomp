; Compact maintained lease boundary. Cdecl far ABI; checked child DS=SS stack.
; No call into bank code between shrink and complete verified restoration.
BITS 16
CPU 8086
%ifdef COMPILER_LEASE_RETAINED
SEGMENT LEASE_CORE public align=16 class=LEASE_MODULE use16
%else
SEGMENT LEASE_CORE public align=16 class=FARCODE use16
%endif
GROUP LEASE_CORE_GROUP LEASE_CORE
extern _compiler_lease_storage
extern _compiler_lease_prepare,_compiler_lease_finalize
extern _compiler_lease_bank_start,_compiler_lease_bank_end
extern _lease_dos_context,_lease_dos_psp,_lease_dos_error
extern _lease_dos_resize,_lease_dos_rewind,_lease_dos_read
%define cookie 0
%define parent 2
%define keep 4
%define full 6
%define owner 8
%define token 10
%define phase 12
%define handle 14
%define crc 16
%define dos_error 18
%define valid 22
%define busy 26
%define buffer 28
%define H(x) cs:_compiler_lease_storage+x
%macro entry 1
global _compiler_lease_%1
_compiler_lease_%1:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 sub sp,6
%endmacro
leave:
 lea sp,[bp-14]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
; All argument access uses the public entry BP. No near helper changes it.
auth:
 cmp word [H(cookie)],0x434c
 jne .identity
 cmp word [H(busy)],0
 jne state
.identity:
 call far _lease_dos_context
 or ax,ax
 jz identity
 cmp word [H(cookie)],0x434c
 jne identity
 mov ax,[bp+6]
 cmp ax,[H(token)]
 jne identity
 mov ax,[bp+8]
 or ax,ax
 jz identity
 cmp ax,[H(parent)]
 je identity
 call far _lease_dos_psp
 cmp ax,[bp+8]
 jne identity
 mov es,ax
 cmp word [es:0],0x20cd
 jne identity
 mov bx,[H(parent)]
 cmp [es:0x16],bx
 jne identity
 dec ax
 mov es,ax
 mov ax,[bp+8]
 cmp [es:1],ax
 jne identity
 xor ax,ax
 ret
state: mov ax,1
 ret
identity: mov ax,2
 ret
; AX PSP / DX extent => AX Boolean, DX preserved. No MCB writes.
block:
 or ax,ax
 jz .bad
 cmp ax,0xa000
 jae .bad
 cmp dx,16
 jb .bad
 mov bx,0xa000
 sub bx,ax
 cmp dx,bx
 ja .bad
 mov bx,ax
 mov es,ax
 cmp word [es:0],0x20cd
 jne .bad
 dec ax
 mov es,ax
 mov al,[es:0]
 cmp al,'M'
 je .type
 cmp al,'Z'
 jne .bad
.type:
 cmp [es:1],bx
 jne .bad
 cmp [es:3],dx
 jne .bad
 mov ax,1
 ret
.bad: xor ax,ax
 ret
; AX segment / CX bytes / DX CRC. Preserves SI/DI/ES/BX.
checksum:
 push bx
 push si
 push es
 mov es,ax
 xor si,si
.byte:
 xor dl,[es:si]
 inc si
 mov bl,8
.bit:
 shr dx,1
 jnc .plain
 xor dx,0xa001
.plain:
 dec bl
 jnz .bit
 loop .byte
 pop es
 pop si
 pop bx
 ret
capture_error:
 call far _lease_dos_error
 mov [H(dos_error)],ax
 ret
entry begin
 call auth
 or ax,ax
 jnz .done
 cmp word [H(phase)],0
 jne .state
 push word [bp+8]
 push word [bp+6]
 call far _compiler_lease_prepare
 add sp,4
 or ax,ax
 jnz .done
 ; Bank frame is gone before shrinking.
 mov word [H(busy)],1
 push word [H(keep)]
 push word [H(parent)]
 call far _lease_dos_resize
 add sp,4
 or ax,ax
 jz .lent
 call capture_error
 mov word [H(phase)],4
 mov word [H(busy)],0
 push word [bp+8]
 push word [bp+6]
 call far _compiler_lease_finalize
 add sp,4
 mov ax,5
 jmp .done
.lent:
 mov word [H(valid)],0
 mov word [H(phase)],2
 mov word [H(busy)],0
 xor ax,ax
 jmp .done
.state: mov ax,1
.done: jmp leave
entry end
 call auth
 or ax,ax
 jnz .done
 mov ax,[bp+8]
 cmp ax,[H(owner)]
 jne .state
 mov ax,[H(phase)]
 cmp ax,4
 je .cleanup
 cmp ax,2
 jb .state
 cmp ax,3
 ja .state
 mov word [H(busy)],1
 mov ax,[H(parent)]
 dec ax
 mov es,ax
 mov dx,[es:3]
 inc ax
 call block
 or ax,ax
 jz .identity
 cmp dx,[H(keep)]
 jb .identity
 cmp dx,[H(full)]
 ja .identity
 je .grown
 push word [H(full)]
 push word [H(parent)]
 call far _lease_dos_resize
 add sp,4
 or ax,ax
 jz .grown
 call capture_error
 mov ax,6
 jmp .retire
.grown:
 mov word [H(phase)],3
 push word [H(handle)]
 call far _lease_dos_rewind
 add sp,2
 or ax,ax
 jnz .io
 mov di,[H(parent)]
 add di,[H(keep)]
 mov si,[H(full)]
 sub si,[H(keep)]
 mov word [bp-20],0xffff ; CRC, below seven saved words.
.read:
 mov bx,si
 cmp bx,256
 jbe .chunk
 mov bx,256
.chunk:
 mov [bp-18],bx
 mov cx,bx
 shl cx,1
 shl cx,1
 shl cx,1
 shl cx,1
 push cx
 push di
 xor ax,ax
 push ax
 push word [H(handle)]
 call far _lease_dos_read
 add sp,8
 cmp ax,cx
 jne .io
 mov ax,di
 mov dx,[bp-20]
 call checksum
 mov [bp-20],dx
 mov bx,[bp-18]
 add di,bx
 sub si,bx
 jnz .read
 mov ax,1
 push ax
 push cs
 mov ax,_compiler_lease_storage+buffer
 push ax
 push word [H(handle)]
 call far _lease_dos_read
 add sp,8
 or ax,ax
 jnz .corrupt
 mov ax,[bp-20]
 cmp ax,[H(crc)]
 jne .corrupt
 mov word [H(valid)],1
 mov word [H(phase)],4
 mov word [H(busy)],0
.cleanup:
 cmp word [H(valid)],1
 jne .state
 mov ax,[H(parent)]
 mov dx,[H(full)]
 call block
 or ax,ax
 jz .state
 push word [bp+8]
 push word [bp+6]
 call far _compiler_lease_finalize
 add sp,4
 jmp .done
.io:
 call capture_error
 mov ax,4
 jmp .retire
.corrupt: mov ax,7
 jmp .retire
.identity: mov ax,2
.retire:
 mov word [H(busy)],0
 jmp .done
.state: mov ax,1
.done: jmp leave
entry info
 mov ax,0xffff
 cmp word [H(cookie)],0x434c
 jne .done
 mov bx,[bp+6]
 cmp bx,10
 jae .bank
 xor ax,ax
 mov al,[cs:info_fields+bx]
 mov bx,ax
 mov ax,[H(bx)]
 jmp .done
.bank:
 cmp bx,10
 jne .offset
 mov ax,seg _compiler_lease_bank_start
 jmp .done
.offset:
 cmp bx,11
 jne .size
 mov ax,_compiler_lease_bank_start
 jmp .done
.size:
 cmp bx,12
 jne .unknown
 mov ax,_compiler_lease_bank_end
 sub ax,_compiler_lease_bank_start
 jmp .done
.unknown:mov ax,0xffff
.done:jmp leave
info_fields: db phase,full,keep,valid,dos_error,crc,parent,owner,handle,24

; Parent cold loader shares the exact same MCB/CRC primitives as restoration.
entry block
global _lease_core_block
_lease_core_block equ _compiler_lease_block
 mov ax,[bp+6]
 mov dx,[bp+8]
 call block
 jmp leave
entry checksum
global _lease_core_checksum
_lease_core_checksum equ _compiler_lease_checksum
 mov dx,[bp+6]
 mov ax,[bp+8]
 mov cx,[bp+10]
 jcxz .done
 call checksum
.done:
 mov ax,dx
 jmp leave
