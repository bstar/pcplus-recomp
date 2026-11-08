; Owned nested DOS child: close inherited handles5..19, never its parent's JFT.
BITS 16
CPU 8086
ORG 100h
 mov ax,[cs:32h]
 mov [own_count],ax
 cmp ax,20
 jb failed
 les si,[cs:34h]
 mov di,own_jft
 call copy20
 mov di,parent_before
 call parent_jft
 xor bx,bx
 mov bx,5
.close:
 cmp byte [cs:own_jft+bx],0ffh
 je .next
 mov ah,3eh
 int 21h
 jc .error
 inc word [closed]
 jmp .next
.error:
 inc word [errors]
.next:
 inc bx
 cmp bx,20
 jb .close
 mov di,parent_after
 call parent_jft
 mov dx,report_name
 mov ax,3d02h
 int 21h
 jnc .opened
 cmp ax,2
 jne failed
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
.opened:
 mov bx,ax
 xor cx,cx
 xor dx,dx
 mov ax,4202h
 int 21h
 jc failed
 mov dx,record
 mov cx,72
 mov ah,40h
 int 21h
 jc failed
 cmp ax,72
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov dx,success_name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,success_text
 mov cx,2
 mov ah,40h
 int 21h
 jc failed
 cmp ax,2
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
parent_jft:
 mov ax,[cs:16h]
 or ax,ax
 jz failed
 mov es,ax
 cmp word [es:0],20cdh
 jne failed
 mov ax,[es:32h]
 mov [cs:parent_count],ax
 cmp ax,20
 jb failed
 les si,[es:34h]
copy20:
 mov cx,20
.copy:
 mov al,[es:si]
 mov [cs:di],al
 inc si
 inc di
 loop .copy
 ret
failed:
 mov ax,4c63h
 int 21h
record: db 'HND1'
own_count: dw 0
parent_count: dw 0
closed: dw 0
errors: dw 0
own_jft: times 20 db 0ffh
parent_before: times 20 db 0ffh
parent_after: times 20 db 0ffh
report_name: db 'HANDLES.BIN',0
success_name: db 'SUCCESS.OK',0
success_text: db 'OK'
