; Passive parent observer. FAIL_BACKUP_DELETE injects one declared DOS error.
BITS 16
CPU 8086
ORG 100h
%include "retire-watch.inc"
%define CAPTURE_SIZE (14+2*FIELD_BYTES+10+20+4000)
jmp start
old_dos: dw 0,0
old_tick: dw 0,0
old_irq: dw 0,0
sample: dw 5254h,0,0,0,0,0,0
before_fields: times FIELD_BYTES db 0
after_fields: times FIELD_BYTES db 0
retire_result: times 10 db 0
account_result: times 20 db 0
notice: times 4000 db 0
dir_name: db 'D:\TEST.DIR',0
setup_name: db 'C:\PRMEDIT.EXE',0
backup_name: db 'D:\PCPBAK.$$$',0
notice_text: db 'Log save error'
fields:
%include "retire-fields.inc"
dos_handler:
 push bp
 mov bp,sp
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 cmp word [cs:sample+12],0
 jne .known
 cmp ah,3dh
 jne .done
 mov si,dx
 mov di,dir_name
 mov cx,12
.name:
 lodsb
 cmp al,[cs:di]
 jne .done
 inc di
 loop .name
 mov [cs:sample+12],ds
.known:
 mov ax,[cs:sample+12]
 mov es,ax
 call observe
 mov ax,[ss:bp-4]
 cmp ah,4bh
 jne .accounting
 cmp word [es:RETIRE],3
 jne .accounting
 mov si,[ss:bp-10]
 mov di,setup_name
 mov cx,15
.setup:
 lodsb
 cmp al,[cs:di]
 jne .accounting
 inc di
 loop .setup
 inc word [cs:sample+8]
.accounting:
 cmp word [es:PROGRAM_KIND],7
 jne .done
 cmp word [es:RETIRE],2
 jne .done
 mov ax,[ss:bp-4]
 cmp ah,3dh
 jb .done
 cmp ah,60h
 ja .done
 inc word [cs:sample+4]
 mov ax,ds
 mov bx,ss
 cmp ax,[cs:sample+12]
 jne .bad
 cmp ax,bx
 jne .bad
 cmp word [es:PROGRAM_PENDING],0
 jne .bad
 cmp word [es:PROGRAM_ACTIVE],1
 jne .bad
 cmp word [es:PROGRAM_STATUS],2
 jne .bad
 cmp word [es:REDISPLAY],0
 jne .bad
 cmp word [es:COMMAND],0
 jne .bad
 cmp word [es:CONNECTION],0
 jne .bad
 in al,21h
 test al,20h
 jz .bad
 mov dx,3ebh
 in al,dx
 test al,80h
 jnz .bad
 mov dx,3e9h
 in al,dx
 or al,al
 jnz .bad
 mov dx,3ech
 in al,dx
 test al,2
 jnz .bad
 push es
 xor ax,ax
 mov es,ax
 mov ax,[es:0dh*4]
 cmp ax,[cs:old_irq]
 jne .vector_bad
 mov ax,[es:0dh*4+2]
 cmp ax,[cs:old_irq+2]
 jne .vector_bad
 pop es
 jmp .fault
.vector_bad:
 pop es
.bad:
 inc word [cs:sample+6]
.fault:
%ifdef FAIL_BACKUP_DELETE
 mov ax,[ss:bp-4]
 cmp ah,41h
 jne .done
 cmp word [cs:sample+10],0
 jne .done
 mov si,[ss:bp-10]
 mov di,backup_name
 mov cx,14
.backup:
 lodsb
 cmp al,[cs:di]
 jne .done
 inc di
 loop .backup
 inc word [cs:sample+10]
 or word [cs:sample+2],16
 mov word [ss:bp-4],5
 or word [ss:bp+6],1
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 pop bp
 iret
%endif
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
 pop bp
 jmp far [cs:old_dos]
tick_handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,[cs:sample+12]
 or ax,ax
 jz .done
 mov es,ax
 call observe
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 jmp far [cs:old_tick]
observe:
 test word [cs:sample+2],1
 jnz .after
 cmp word [es:PROGRAM_KIND],7
 jne .done
 cmp word [es:RETIRE],2
 jne .done
 mov di,before_fields
 call copy_fields
 or word [cs:sample+2],1
.after:
 mov ax,[es:RETIRE]
 cmp ax,3
 je .finished
 cmp ax,4
 jne .done
.finished:
 test word [cs:sample+2],2
 jnz .returned
 mov di,after_fields
 call copy_fields
 mov si,RETIRE
 mov di,retire_result
 mov cx,10
 call copy_bytes
 mov si,ACCOUNT
 mov di,account_result
 mov cx,20
 call copy_bytes
 or word [cs:sample+2],2
.returned:
 cmp word [es:PROGRAM_ACTIVE],0
 jne .done
 cmp word [es:PROGRAM_PENDING],0
 jne .done
 mov dx,3e9h
 in al,dx
 cmp al,1
 jne .done
 in al,21h
 test al,20h
 jnz .done
 or word [cs:sample+2],4
 cmp word [es:RETIRE],4
 jne .done
 test word [cs:sample+2],8
 jnz .done
 push es
 mov ax,0b800h
 mov es,ax
 mov si,24*160+2
 mov di,notice_text
 mov cx,14
.text:
 mov al,[es:si]
 cmp al,[cs:di]
 jne .no_notice
 add si,2
 inc di
 loop .text
 xor si,si
 mov di,notice
 mov cx,4000
 call copy_bytes
 or word [cs:sample+2],8
.no_notice:
 pop es
.done: ret
copy_fields:
 mov bx,fields
 mov dx,FIELD_COUNT
.next:
 mov si,[cs:bx]
 mov cx,[cs:bx+2]
 call copy_bytes
 add bx,4
 dec dx
 jnz .next
 ret
copy_bytes:
 mov al,[es:si]
 mov [cs:di],al
 inc si
 inc di
 loop copy_bytes
 ret
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_tick],bx
 mov [old_tick+2],es
 mov ax,3521h
 int 21h
 mov [old_dos],bx
 mov [old_dos+2],es
 mov ax,350dh
 int 21h
 mov [old_irq],bx
 mov [old_irq+2],es
 mov dx,dos_handler
 mov ax,2521h
 int 21h
 mov dx,tick_handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,tick_handler
 jne failed
 cmp word [es:sample],5254h
 jne failed
 mov si,sample
 mov di,buffer
 mov cx,CAPTURE_SIZE
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old_dos]
 mov ax,[es:old_dos+2]
 push ds
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 mov dx,[es:old_tick]
 mov ax,[es:old_tick+2]
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,CAPTURE_SIZE
 mov ah,40h
 int 21h
 jc close_failed
 cmp ax,CAPTURE_SIZE
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
buffer: times CAPTURE_SIZE db 0
filename: db 'D:\RETIRE.BIN',0
