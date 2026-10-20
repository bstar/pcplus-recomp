; Test-only BIOS keyboard helper: Alt-X ten seconds after the final file-menu
; footer is visible. No application state or serial replies are injected.
bits 16
cpu 8086
org 100h
jmp install
old_vector: dd 0
state: db 0
ticks: dw 0
prompt: db 'File Base >>',0
handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 cmp byte [state],0
 jne .count
 mov ax,0b800h
 mov es,ax
 xor di,di
.search:
 push di
 mov si,prompt
.match:
 lodsb
 or al,al
 jz .found
 cmp di,4000
 jae .miss
 cmp al,[es:di]
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,4000
 jb .search
 jmp .done
.found:
 pop di
 mov byte [state],1
 mov word [ticks],180
 jmp .done
.count:
 cmp byte [state],1
 jne .done
 dec word [ticks]
 jnz .done
 mov cx,2d00h
 mov ah,5
 int 16h
 or al,al
 jz .restore
 inc word [ticks]
 jmp .done
.restore:
 mov byte [state],2
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[old_vector]
 mov [es:70h],ax
 mov ax,[old_vector+2]
 mov [es:72h],ax
 popf
.done:
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_vector]
resident_end:
filename: db 'D:\KEYOLD.BIN',0
install:
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ah,3ch
 xor cx,cx
 mov dx,filename
 int 21h
 jc failure
 mov bx,ax
 mov ah,40h
 mov cx,4
 mov dx,old_vector
 int 21h
 pushf
 push ax
 mov ah,3eh
 int 21h
 pop ax
 popf
 jc failure
 cmp ax,4
 jne failure
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
failure:
 mov ax,4c01h
 int 21h
