; Test-only passive INT21 observer. Records the first TEST.DIR content-open
; path and mode. No path, CWD, keyboard, UART, file-call or product mutation.
BITS 16
CPU 8086
ORG 100h
jmp start
old_dos: dw 0,0
sample: dw 4944h,0,0
first_path: times 64 db 0
dos_handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 cmp ah,3dh
 jne .done
 mov bx,ax
 mov si,dx
 xor di,di
 mov cx,64
.scan:
 lodsb
 or al,al
 jz .end
 inc di
 loop .scan
 jmp .done
.end:
 cmp di,8
 jb .done
 cmp word [si-9],'TE'
 jne .done
 cmp word [si-7],'ST'
 jne .done
 cmp word [si-5],'.D'
 jne .done
 cmp word [si-3],'IR'
 jne .done
 inc word [cs:sample+2]
 cmp word [cs:sample+2],1
 jne .done
 mov [cs:sample+4],bx
 mov si,dx
 mov di,first_path
 mov cx,64
.copy:
 lodsb
 mov [cs:di],al
 inc di
 or al,al
 loopnz .copy
.done:
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_dos]
resident_end:
start:
 mov ax,3521h
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_dos],bx
 mov [old_dos+2],es
 mov dx,dos_handler
 mov ax,2521h
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,dos_handler
 jne failed
 cmp word [es:sample],4944h
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,70
.save:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .save
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 mov [expected],dx
 mov [expected+2],ax
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov ax,3521h
 int 21h
 cmp bx,[expected]
 jne failed
 mov ax,es
 cmp ax,[expected+2]
 jne failed
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,70
 mov ah,40h
 int 21h
 jc close_failed
 cmp ax,70
 jne close_failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
close_failed:
 mov ah,3eh
 int 21h
failed:
 mov ax,4c01h
 int 21h
expected: dw 0,0
buffer: times 70 db 0
filename: db 'D:\IDENTITY.BIN',0
