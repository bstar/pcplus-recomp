; Meta bank DOS kernel boundaries: near cdecl, DS=SS. Private deny-write
; reads, exclusive create, no-overwrite rename; no DOS SDK/CRT near imports.
BITS 16
CPU 8086
SEGMENT META_EDITOR_CODE public align=16 class=FARCODE use16
%ifdef META_BANK_TEST_FAULTS
%define _key_file_attr _key_real_attr
%define _key_file_open _key_real_open
%define _key_file_create _key_real_create
%define _key_file_read _key_real_read
%define _key_file_write _key_real_write
%define _key_file_close _key_real_close
%define _key_file_rename _key_real_rename
%define _key_file_delete _key_real_delete
%endif
%macro enter 0
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ds
%endmacro
%macro leave 0
 pop ds
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
%endmacro
global _key_file_attr,_key_file_open,_key_file_create
 global _key_file_read,_key_file_write,_key_file_close,_key_file_rename,_key_file_delete
_key_file_attr:
 enter
 mov dx,[bp+4]
 mov ax,4300h
 int 21h
 jc .done
 mov bx,[bp+6]
 mov [bx],cx
 xor ax,ax
.done:
 leave
_key_file_open:
 enter
 mov ax,[bp+6]
 and ax,0ff7fh ; O_RDONLY with optional O_NOINHERIT only
 jnz .bad
 mov dx,[bp+4]
 mov ax,3da0h ; read only, deny writes, private descriptor
 int 21h
 jc .done
 mov bx,[bp+8]
 mov [bx],ax
 xor ax,ax
 jmp .done
.bad:
 mov ax,1
.done:
 leave
_key_file_create:
 enter
 mov dx,[bp+4]
 mov cx,[bp+6]
 mov ah,5bh
 int 21h
 jc .done
 mov bx,[bp+8]
 mov [bx],ax
 xor ax,ax
.done:
 leave
%macro io 2
%1:
 enter
 mov bx,[bp+4]
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ah,%2
 int 21h
 jc .done
 mov bx,[bp+10]
 mov [bx],ax
 xor ax,ax
.done:
 leave
%endmacro
io _key_file_read,3fh
io _key_file_write,40h
_key_file_close:
 enter
 mov bx,[bp+4]
 mov ah,3eh
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
_key_file_rename:
 enter
 push ds
 pop es
 mov dx,[bp+4]
 mov di,[bp+6]
 mov ah,56h
 int 21h
 jc .done
 xor ax,ax
.done:
 leave
_key_file_delete:
 enter
 mov dx,[bp+4]
 mov ah,41h
 int 21h
 jc .done
 xor ax,ax
.done:
 leave

; find_t is the caller's DOS 43-byte DTA. DOS continuation data remains there.
; Restore the previously selected DTA on success, error18 and every failure.
global _meta_scan_fs_first,_meta_scan_fs_next
_meta_scan_fs_first:
 enter
 mov si,1
 jmp short meta_find
_meta_scan_fs_next:
 enter
 xor si,si
meta_find:
 mov ah,2fh
 int 21h
 push es
 push bx
 or si,si
 jz .next_dta
 mov dx,[bp+6]
 jmp short .set_dta
.next_dta:
 mov dx,[bp+4]
.set_dta:
 mov ah,1ah
 int 21h
 or si,si
 jz .next
 mov dx,[bp+4]
 xor cx,cx
 mov ah,4eh
 jmp short .find
.next:
 mov ah,4fh
.find:
 int 21h
 jc .error
 xor ax,ax
.error:
 pop dx
 pop ds
 push ax
 mov ah,1ah
 int 21h
 pop ax
 leave
