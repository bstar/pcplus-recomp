; Passive test-only file-open witness. No additional DOS/BIOS requests,
; product writes, timer sampling or terminal replies inside the hook.
BITS 16
CPU 8086
ORG 0x100
jmp start
old21: dd 0
data: dw 0x5357,1,0,0
records: times 4*4016 db 0
pre_name: db 'D:\FPRE.TXT',0
post_name: db 'D:\FPST.TXT',0
hook:
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
 cmp word [cs:data+4],4
 jae .done
 cmp ax,0x6c00
 jne .ordinary
 mov dx,si
 jmp .bind
.ordinary:
 cmp ah,0x3c
 je .bind
 cmp ah,0x3d
 jne .done
.bind:
 ; The actual IRQ entry identifies the retained parent's load segment.
 xor ax,ax
 mov es,ax
 cmp word [es:IRQ_VECTOR],CHILD_ISR_OFFSET
 je .from_child
 cmp word [es:IRQ_VECTOR],PARENT_ISR_OFFSET
 jne .done
 mov ax,[es:IRQ_VECTOR+2]
 sub ax,PARENT_ISR_SEG
 add ax,PARENT_RENDER_SEG
 mov es,ax
 mov ax,[es:PARENT_CHILD_DS]
 jmp .bound
.from_child:
 mov ax,[es:IRQ_VECTOR+2]
 sub ax,CHILD_ISR_SEG
 add ax,CHILD_DATA_SEG
.bound:
 mov bx,ds
 cmp ax,bx
 jne .done
 mov ax,ss
 cmp ax,bx
 jne .done
 cmp dx,0xfff4
 ja .done
 mov si,dx
 mov di,pre_name
 test word [cs:data+4],1
 jz .name
 mov di,post_name
.name:
 mov cx,12
.compare:
 mov al,[si]
 cmp al,[cs:di]
 jne .done
 inc si
 inc di
 loop .compare
 mov ax,[cs:data+4]
 mov bx,4016
 mul bx
 mov di,ax
 add di,records
 mov ax,[cs:data+4]
 mov [cs:di],ax
 mov ax,0x40
 mov ds,ax
 xor ax,ax
 mov al,[0x49]
 cmp al,3
 je .color
 cmp al,7
 jne .done
 mov bp,0xb000
 jmp .mode
.color:
 mov bp,0xb800
.mode:
 mov [cs:di+2],ax
 mov ax,[0x4a]
 mov [cs:di+4],ax
 xor ax,ax
 mov al,[0x84]
 inc ax
 mov [cs:di+6],ax
 mov ax,[0x85]
 mov [cs:di+8],ax
 mov ax,[0x50]
 mov [cs:di+10],ax
 mov ax,[0x60]
 mov [cs:di+12],ax
 xor ax,ax
 mov al,[0x62]
 mov [cs:di+14],ax
 or ax,ax
 jnz .done
 mov ax,bp
 mov ds,ax
 push cs
 pop es
 add di,16
 xor si,si
 mov cx,2000
 cld
 rep movsw
 inc word [cs:data+4]
.done:
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
 jmp far [cs:old21]
resident_end:
start:
 mov ax,0x3521
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old21],bx
 mov [old21+2],es
 mov [data+6],cs
 mov dx,hook
 mov ax,0x2521
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,hook
 jne failed
 cmp word [es:data],0x5357
 jne failed
 mov dx,[es:old21]
 mov ax,[es:old21+2]
 push ds
 mov ds,ax
 mov ax,0x2521
 int 0x21
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 push ds
 push es
 pop ds
 mov dx,data
 mov cx,8+4*4016
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,8+4*4016
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\SSCREEN.BIN',0
