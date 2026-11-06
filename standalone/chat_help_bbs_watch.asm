; Passive BIOS/timer observer of editor -> Chat -> Help -> Chat -> editor.
; Hooks write only their own storage. No DOS/BIOS calls in either callback.
BITS 16
CPU 8086
ORG 100h
jmp start
old10: dd 0
old1c: dd 0
; magic,phase,before_seen,ticks,parentDS,rows; five cursor positions;
; five cursor shapes; Help owner/parser/wait/PROGRAM active/kind;
; Chat return owner/parser/wait; before/after BIOS mode+columns.
report: times 26 dw 0
frames: times 20000 db 0xa5
last: dw 0
stable: dw 0
editor_prompt: db 'KEYTEST',0
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
editor_visible:
 xor di,di
.search:
 mov si,editor_prompt
 push di
.match:
 lodsb
 or al,al
 jz .found
 cmp di,3840
 jae .miss
 cmp al,[es:di]
 jne .miss
 add di,2
 jmp .match
.miss:
 pop di
 add di,2
 cmp di,3840
 jb .search
 clc
 ret
.found:
 pop di
 stc
 ret
; DI=destination. ES=B800, DS=CS.
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
hook10:
 pushf
 cmp ah,3
 jne .chain
 save
 cmp word [report+2],0
 jne .done
 mov ax,ss
 mov bp,sp
 mov dx,[ss:bp+2] ; interrupted DS, below saved ES
 cmp ax,dx
 jne .done
 add ax,FROZEN_DELTA
 mov es,ax
 cmp word [es:5],0x4f4c
 jne .done
 cmp word [es:7],0x4343
 jne .done
 cmp word [es:13],CHAT_API_VERSION
 jne .done
 mov ax,ss
 mov [report+8],ax
 mov ax,0x40
 mov es,ax
 cmp word [es:0x49],0x5003
 jne .done
 cmp byte [es:0x84],24
 jne .done
 mov ax,0xb800
 mov es,ax
 call editor_visible
 jnc .done
 mov di,frames
 call copy
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [report+12],ax
 mov ax,[es:0x60]
 mov [report+22],ax
 mov word [report+48],0x5003
 mov word [report+4],1
.done:
 restore
.chain:
 popf
 jmp far [cs:old10]
hook1c:
 pushf
 save
 inc word [report+6]
 cmp word [report+4],1
 jne .done
 cmp word [report+2],4
 jae .done
 mov ax,[report+8]
 or ax,ax
 jz .done
 mov es,ax
 mov bx,[report+2]
 cmp bx,1
 je .helper
 cmp word [es:ACTIVE_OFF],0
 jne .done
 cmp bx,3
 je .editor
 cmp word [es:OWNER_OFF],2
 jne .done
 mov ax,0xb800
 mov es,ax
 cmp byte [es:72],'R'
 jne .done
 cmp byte [es:74],'E'
 jne .done
 cmp byte [es:76],'M'
 jne .done
 cmp byte [es:3200],'X'
 jne .done
 jmp .candidate
.helper:
 mov ax,0xb800
 mov es,ax
 cmp byte [es:2],'C'
 jne .done
 cmp byte [es:4],'h'
 jne .done
 cmp byte [es:6],'a'
 jne .done
 jmp .candidate
.editor:
 cmp word [es:OWNER_OFF],0
 jne .done
 mov ax,0xb800
 mov es,ax
 call editor_visible
 jnc .done
.candidate:
 mov ax,0x40
 mov es,ax
 cmp word [es:0x49],0x5003
 jne .done
 cmp byte [es:0x84],24
 jne .done
 mov word [report+10],25
 mov ax,0xb800
 mov es,ax
 mov cx,2000
 xor si,si
 xor dx,dx
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 cmp dx,[last]
 je .same
 mov [last],dx
 mov word [stable],0
 jmp .done
.same:
 inc word [stable]
 cmp word [stable],2
 jb .done
 mov bx,[report+2]
 inc bx
 mov ax,bx
 shl bx,1
 push ax
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [report+12+bx],ax
 mov ax,[es:0x60]
 mov [report+22+bx],ax
 pop ax
 mov dx,4000
 mul dx
 mov di,frames
 add di,ax
 mov ax,0xb800
 mov es,ax
 call copy
 mov ax,[report+8]
 mov es,ax
 cmp word [report+2],1
 jne .not_help
 mov ax,[es:OWNER_OFF]
 mov [report+32],ax
 mov ax,[es:PARSER_OFF]
 mov [report+34],ax
 mov ax,[es:WAIT_OFF]
 mov [report+36],ax
 mov ax,[es:ACTIVE_OFF]
 mov [report+38],ax
 mov ax,[es:KIND_OFF]
 mov [report+40],ax
.not_help:
 cmp word [report+2],2
 jne .not_chat_return
 mov ax,[es:OWNER_OFF]
 mov [report+42],ax
 mov ax,[es:PARSER_OFF]
 mov [report+44],ax
 mov ax,[es:WAIT_OFF]
 mov [report+46],ax
.not_chat_return:
 cmp word [report+2],3
 jne .not_editor_return
 mov word [report+50],0x5003
.not_editor_return:
 inc word [report+2]
 mov word [stable],0
.done:
 restore
 popf
 jmp far [cs:old1c]
resident_end:
start:
 mov ax,0x3510
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old10],bx
 mov [old10+2],es
 mov ax,0x351c
 int 0x21
 mov [old1c],bx
 mov [old1c+2],es
 mov word [report],0x4845
 mov dx,hook10
 mov ax,0x2510
 int 0x21
 mov dx,hook1c
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,hook10
 jne failed
 cmp word [es:report],0x4845
 jne failed
 push es
 mov ax,0x351c
 int 0x21
 cmp bx,hook1c
 mov ax,es
 pop es
 jne failed
 mov dx,es
 cmp ax,dx
 jne failed
 pushf
 cli
 mov si,report
 mov di,buffer
 mov cx,20052
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 push es
 mov dx,[es:old10]
 mov ax,[es:old10+2]
 push ds
 mov ds,ax
 mov ax,0x2510
 int 0x21
 pop ds
 pop es
 mov dx,[es:old1c]
 mov ax,[es:old1c+2]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,20052
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,20052
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
name: db 'D:\BBHELP.BIN',0
buffer: times 20052 db 0
