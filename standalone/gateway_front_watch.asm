; Independent test-only BIOS/VGA observer, no product memory or DOS in hooks.
BITS 16
CPU 8086
ORG 0x100
jmp start
old10: dd 0
old2f: dd 0
report: dw 0x474f,0,0,0,0,0,0,0,0,0,0,0
frames: times 16000 db 0
%macro save 0
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 push cs
 pop ds
%endmacro
%macro restore 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
%endmacro
hook10:
 pushf
 cmp ah,0x0f
 je .before
 cmp ah,2
 je .after
.chain:
 popf
 jmp far [cs:old10]
.before:
 save
 cmp word [report+4],0
 jne .before_done
 mov ax,0x40
 mov es,ax
 cmp word [es:0x50],0x020a
 jne .before_done
 cmp word [es:0x49],0x5003
 jne .before_done
 mov ax,[es:0x50]
 mov [report+12],ax
 mov ax,[es:0x60]
 cmp ah,0x20
 je .before_done
 mov [report+16],ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [report+8],ax
 mov word [report+20],0x5003
 mov ax,0xb800
 mov es,ax
 cmp word [es:328],0x0742 ; B in BEFORE at row3,column5.
 jne .before_done
 cmp word [es:330],0x0745
 jne .before_done
 mov di,frames
 call copy
 mov word [report+2],1
.before_done:
 restore
 jmp .chain
.after:
 save
 cmp word [report+2],1
 jne .after_done
 cmp word [report+4],1
 jne .after_done
 cmp word [report+6],0
 jne .after_done
 cmp dx,[report+12]
 jne .after_done
 mov [report+14],dx
 mov ax,0x40
 mov es,ax
 cmp word [es:0x49],0x5003
 jne .after_done
 mov ax,[es:0x60]
 mov [report+18],ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 mov [report+10],ax
 mov word [report+22],0x5003
 mov ax,0xb800
 mov es,ax
 cmp word [es:328],0x0742
 jne .after_done
 cmp word [es:330],0x0745
 jne .after_done
 mov di,frames+8000
 call copy
 mov word [report+6],1
.after_done:
 restore
 jmp .chain
copy:
 xor si,si
 mov cx,4000
.word:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .word
 ret
hook2f:
 cmp ax,0xd741
 jne .chain
 cmp bx,1
 je .mark
 push cs
 pop es
 mov di,report
 iret
.mark:
 mov word [cs:report+4],1
 iret
.chain:
 jmp far [cs:old2f]
resident_end:
start:
 cmp byte [0x82],'T'
 je install
 mov ax,0xd741
 cmp byte [0x82],'M'
 je mark
 xor bx,bx
 int 0x2f
 cmp word [es:di],0x474f
 jne failed
 mov si,di
 push es
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 pop es
 jc failed
 mov bx,ax
 push ds
 mov ax,es
 mov ds,ax
 mov dx,si
 mov cx,16024
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,16024
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
mark:
 mov bx,1
 int 0x2f
 mov ax,0x4c00
 int 0x21
install:
 mov ax,0x3510
 int 0x21
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x352f
 int 0x21
 mov [old2f],bx
 mov [old2f+2],es
 mov dx,hook10
 mov ax,0x2510
 int 0x21
 mov dx,hook2f
 mov ax,0x252f
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
name: db 'D:\GWVIEW.BIN',0
