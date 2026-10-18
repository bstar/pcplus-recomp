; Maintained bounded pure directory statistics update. DS=SS, near C caller12.
; unsigned directory_accounting_patch(src114,dst114,year,month,day,delta)
; AX:0 success,1 extent/active-frame overlap,2 invalid Gregorian DOS date.
; Only date+count61..71 differ. Original Y2K overwrite is intentionally fixed.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _directory_accounting_patch,directory_accounting_patch
_directory_accounting_patch:
directory_accounting_patch:
 push bp
 mov bp,sp
 sub sp,114
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cld
 ; Reject a wrapping record or a buffer aliasing this active call frame.
 mov si,[bp+4]
 call .extent
 jc .extent_error
 mov si,[bp+6]
 call .extent
 jc .extent_error
 mov ax,[bp+8]
 cmp ax,1980
 jb .date_error
 cmp ax,2099
 ja .date_error
 mov bx,[bp+10]
 dec bx
 cmp bx,11
 ja .date_error
 mov cx,31
 cmp bx,1
 je .february
 cmp bx,3
 je .thirty
 cmp bx,5
 je .thirty
 cmp bx,8
 je .thirty
 cmp bx,10
 jne .day
.thirty:
 mov cx,30
 jmp short .day
.february:
 mov cx,28
 test ax,3 ;1980..2099: every fourth year is Gregorian leap, including2000.
 jnz .day
 inc cx
.day:
 mov dx,[bp+12]
 or dx,dx
 jz .date_error
 cmp dx,cx
 ja .date_error
 push ss
 pop es
 mov si,[bp+4]
 lea di,[bp-114]
 mov cx,114
 rep movsb
 lea di,[bp-114+61]
 mov ax,[bp+10]
 call .two_digits
 mov byte [di],'/'
 inc di
 mov ax,[bp+12]
 call .two_digits
 mov byte [di],'/'
 inc di
 mov ax,[bp+8]
 xor dx,dx
 mov bx,100
 div bx
 mov ax,dx
 call .two_digits
 mov byte [di],0
 mov ax,[bp+14]
 add [bp-114+70],ax ;Intentional original16-bit modular counter behavior.
 lea si,[bp-114]
 mov di,[bp+6]
 mov cx,114
 rep movsb
 xor ax,ax
 jmp short .done
.extent_error:
 mov ax,1
 jmp short .done
.date_error:
 mov ax,2
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 ret
.two_digits:
 mov bl,10
 div bl
 add al,'0'
 mov [di],al
 inc di
 add ah,'0'
 mov [di],ah
 inc di
 ret
.extent:
 cmp si,65422
 ja .bad_extent
 lea ax,[bp+16]
 cmp si,ax
 jae .good_extent
 lea ax,[si+114]
 lea dx,[bp-128] ;Scratch + saved registers + internal return address.
 cmp ax,dx
 ja .bad_extent
.good_extent:
 clc
 ret
.bad_extent:
 stc
 ret
