; Passive File Directory/editor observer: BIOS/VGA reads and private query only.
; No product memory, DOS calls or synthesized screen/terminal replies in hooks.
BITS 16
CPU 8086
ORG 0x100
jmp start
old10: dd 0
old2f: dd 0
%ifdef FILE_VIEWER_ROUNDTRIP
%define REPORT_MAGIC 0x5657
%define REPORT_QUERY 0xd743
%define DETAIL_BYTES 4000
%define REPORT_BYTES 12024
%else
%define REPORT_MAGIC 0x464f
%define REPORT_QUERY 0xd742
%define DETAIL_BYTES 320
%define REPORT_BYTES 8344
%endif
report: dw REPORT_MAGIC,0,0,0,0,0,0,0,0,0,0,0
frames: times 8000 db 0
listing: times DETAIL_BYTES db 0
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
 cld
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
 call editor_visible
 jnc .before_done
 mov di,frames
 call copy
 mov word [report+2],1
.before_done:
 restore
 jmp .chain
.after:
 save
 call observe_listing
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
 call editor_visible
 jnc .after_done
 mov di,frames+4000
 call copy
 mov word [report+6],1
.after_done:
 restore
 jmp .chain
copy:
 xor si,si
 mov cx,2000
.word:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .word
 ret
observe_listing:
 cmp word [report+2],1
 jne .done
 cmp word [report+4],0
 jne .done
 mov ax,0xb800
 mov es,ax
%ifdef FILE_VIEWER_ROUNDTRIP
 cmp word [es:0],0756h
 jne .done
 cmp word [es:2],0749h
 jne .done
 cmp word [es:4],0745h
 jne .done
 cmp word [es:3842],7148h
 jne .done
 xor si,si
 mov di,listing
 mov cx,2000
.view_page:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .view_page
%else
 cmp word [es:364],0x0746 ; FILE NAME
 jne .done
 cmp word [es:684],0x0754 ; TEST.PRM
 jne .done
 cmp word [es:686],0x0745
 jne .done
 cmp word [es:688],0x0753
 jne .done
 mov si,320
 mov di,listing
 mov cx,80
.header:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .header
 mov si,640
 mov cx,80
.entry:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .entry
%endif
 mov word [report+4],1
.done:
 ret
hook2f:
 cmp ax,REPORT_QUERY
 jne .chain
 or bx,bx
 jne .chain
 push cs
 pop es
 mov di,report
 iret
.chain:
 jmp far [cs:old2f]
; Require the actual stock subject marker, regardless of its row.
editor_prompt: db 'KEYTEST',0
editor_visible:
 push si
 xor di,di
.search:
 mov si,editor_prompt
 push di
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
 pop si
 clc
 ret
.found:
 pop di
 pop si
 stc
 ret
resident_end:
start:
 cmp byte [0x82],'T'
 je install
 mov ax,REPORT_QUERY
 xor bx,bx
 int 0x2f
 cmp word [es:di],REPORT_MAGIC
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
 mov cx,REPORT_BYTES
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,REPORT_BYTES
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
install:
%ifdef FILE_VIEWER_ROUNDTRIP
 mov dx,view_name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,view_data
 mov cx,view_end-view_data
 mov ah,40h
 int 21h
 jc failed
 cmp ax,view_end-view_data
 jne failed
 mov ah,3eh
 int 21h
 jc failed
%endif
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
%ifdef FILE_VIEWER_ROUNDTRIP
name: db 'D:\VFVIEW.BIN',0
view_name: db 'D:\VIEW.DAT',0
view_data: db 'VIEWER CHECK',13,10,'READ ONLY / CP437: ',0dbh,0b1h,0c4h,13,10,'Editor stays active.',13,10
view_end:
%else
name: db 'D:\FDVIEW.BIN',0
%endif
