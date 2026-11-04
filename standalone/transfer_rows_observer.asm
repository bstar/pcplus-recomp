; Passive selected-image INT10 witness. Chains the real BIOS; no product writes,
; no key injection, no DOS calls while observing. At most two transfer leases.
BITS 16
CPU 8086
ORG 100h
jmp start
old10: dw 0,0
phase: dw 0
sample:
magic: dw 0x5254,1
before_count: dw 0
after_count: dw 0
ui_seen: times 2 dw 0
before_store: times 2*334 db 0
after_store: times 2*334 db 0
ui_store: times 2*320 db 0
sample_end:
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
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
 popf
%endmacro
handler:
 save
 cld
 mov bp,sp
 mov ax,ss
 mov bx,ds
 cmp ax,bx
 jne .chain
 cmp ax,DGROUP_REL+0x10
 jb .chain
 sub ax,DGROUP_REL+0x10
 cmp ax,[PROCESS_PSP]
 jne .chain
 add ax,UI_CS+0x10
 cmp ax,[ss:bp+22]
 jne .chain
 mov ax,[ss:bp+20]
 cmp ax,READ_SITE
 jne .restore_check
 cmp byte [ss:bp+17],3
 jne .chain
 cmp word [cs:before_count],2
 jae .chain
 mov word [cs:phase],0
 jmp .wrapped
.restore_check:
 cmp ax,RESTORE_SITE+18
 jne .prompt_check
 cmp byte [ss:bp+17],2
 jne .chain
 cmp word [cs:after_count],2
 jae .chain
 mov word [cs:phase],1
.wrapped:
 restore
 pushf
 call far [cs:old10]
 save
 cld
 push cs
 pop ds
 mov ax,[before_count]
 mov di,before_store
 cmp word [phase],0
 jne .after
 inc word [before_count]
 jmp .record
.after:
 mov ax,[after_count]
 mov di,after_store
 inc word [after_count]
.record:
 mov cx,334
 mul cx
 add di,ax
 call record
 ; Keep caller IF/DF when propagating BIOS condition flags. Our PUSHF/far-call
 ; frame begins inside an interrupt and must not disable the application's IF.
 mov bp,sp
 mov ax,[ss:bp+18]
 and ax,0xf9ff
 mov dx,[ss:bp+24]
 and dx,0x0600
 or ax,dx
 mov [ss:bp+24],ax
 restore
 iret
.prompt_check:
 cmp ax,PROMPT_SITE
 jne .chain
 cmp byte [ss:bp+17],2
 jne .chain
 cmp word [PROTOCOL],EXPECTED_PROTOCOL
 jne .chain
 cmp byte [VISIBLE],1
 jne .chain
 mov bx,[cs:before_count]
 or bx,bx
 jz .chain
 cmp bx,2
 ja .chain
 dec bx
 shl bx,1
 cmp word [cs:ui_seen+bx],0
 jne .chain
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 cmp ax,EXPECTED_ROWS
 jne .chain
 sub ax,2
 mov cx,160
 mul cx
 mov si,ax
 mov di,ax
 inc di
 mov ax,0xb800
 mov es,ax
 mov cx,160
.attrs:
 cmp byte [es:di],0x1f
 jne .chain
 add di,2
 loop .attrs
 mov word [cs:ui_seen+bx],1
 mov ax,bx
 shr ax,1
 mov cx,320
 mul cx
 mov di,ui_store
 add di,ax
 push cs
 pop ds
 mov cx,320
.ui_copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .ui_copy
.chain:
 restore
 jmp far [cs:old10]
record:
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 or ax,ax
 jz .legacy
 inc ax
 jmp .rows
.legacy:
 mov ax,25
.rows:
 mov [di+320],ax
 cmp ax,25
 jb .done
 cmp ax,50
 ja .done
 sub ax,2
 mov dx,160
 mul dx
 mov si,ax
 mov ax,[es:0x85]
 mov [di+322],ax
 mov ax,[es:0x50]
 mov [di+324],ax
 mov ax,[es:0x60]
 mov [di+326],ax
 xor ax,ax
 mov al,[es:0x49]
 mov [di+328],ax
 mov ax,[es:0x4a]
 mov [di+330],ax
 xor ax,ax
 mov al,[es:0x62]
 mov [di+332],ax
 mov ax,0xb800
 mov es,ax
 mov cx,320
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
.done:
 ret
resident_end:
start:
 mov ax,0x3510
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old10],bx
 mov [old10+2],es
 mov dx,handler
 mov ax,0x2510
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:magic],0x5254
 jne failed
 mov ax,[es:old10]
 mov [saved10],ax
 mov ax,[es:old10+2]
 mov [saved10+2],ax
 pushf
 cli
 push ds
 mov ax,es
 mov ds,ax
 push cs
 pop es
 mov si,sample
 mov di,buffer
 mov cx,sample_end-sample
 rep movsb
 pop ds
 popf
 push ds
 mov dx,[saved10]
 mov ds,[saved10+2]
 mov ax,0x2510
 int 0x21
 pop ds
 mov ah,0x3c
 xor cx,cx
 mov dx,output
 int 0x21
 jc failed
 mov bx,ax
 mov ah,0x40
 mov cx,sample_end-sample
 mov dx,buffer
 int 0x21
 jc failed
 cmp ax,sample_end-sample
 jne failed
 mov ah,0x3e
 int 0x21
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
saved10: dw 0,0
output: db 'TRWATCH.BIN',0
buffer: times sample_end-sample db 0
