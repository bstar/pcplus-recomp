BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT NOTICECODE public class=CODE use16
global _notice_fault_raise,_notice_fault_save
extern _notice_fault_report
_notice_fault_raise:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 cmp ax,1
 jne .divide
 call far _notice_fault_abort
.divide:
 cmp ax,2
 jne .valid_ds
 mov ax,0x40
 mov ds,ax
.valid_ds:
 xor ax,ax
 xor dx,dx
 xor bx,bx
 div bx
 pop bp
 ret ; a real fault must bypass this return
_notice_fault_save:
 push bx
 push si
 xor cx,cx
 mov dx,filename
 mov ah,0x3c
 int 0x21
 jc .bad
 mov bx,ax
 mov cx,58
 mov dx,_notice_fault_report
 mov ah,0x40
 int 0x21
 mov si,1
 jc .close
 cmp ax,58
 jne .close
 xor si,si
.close:
 mov ah,0x3e
 int 0x21
 jnc .status
 mov si,1
.status:
 mov ax,si
 jmp short .done
.bad:
 mov ax,1
.done:
 pop si
 pop bx
 retf
SEGMENT _TEXT public class=CODE use16
global _notice_fault_abort
extern _runtime_set_error,aspect_abort
_notice_fault_abort:
 mov ax,5
 push ax
 call _runtime_set_error
 add sp,2
 jmp aspect_abort
SEGMENT _DATA public class=DATA use16
filename: db 'NOTICE.BIN',0
