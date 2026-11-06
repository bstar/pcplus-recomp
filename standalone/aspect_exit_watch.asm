; Test-only passive INT21 witness. No additional DOS requests or product writes
; inside the hook. Captures only a child bound by the parent's render lease.
BITS 16
CPU 8086
ORG 0x100
jmp start
old21: dd 0
parent_ds: dw 0
data: dw 0xae51,2,0,0,0
records: times 8*13 dw 0
alloc_data: dw 0xa148,1,0
alloc_records: times 16*4 dw 0
alloc_current: dw 0
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
 cmp ah,0x48
 je .allocate
 cmp ax,0x4b00
 je .exec
 cmp ah,0x4c
 jne .done
 cmp word [cs:parent_ds],0
 je .done
 mov bx,[cs:parent_ds]
 sub bx,PARENT_DATA_SEG
 add bx,PARENT_RENDER_SEG
 mov es,bx
 mov bx,[es:PARENT_CHILD_DS]
 mov cx,ds
 cmp cx,bx
 jne .done
 mov bx,ss
 cmp bx,cx
 jne .done
 mov bx,[cs:data+4]
 cmp bx,8
 jae .done
 inc word [cs:data+4]
 mov di,bx
 shl bx,1
 shl di,1
 shl di,1
 add di,bx
 shl di,1
 shl di,1
 add di,bx ; index*26
 add di,records
 xor ah,ah
 mov [cs:di],ax
 mov [cs:di+2],ds
 mov [cs:di+4],ss
 mov ax,[CHILD_ERROR]
 mov [cs:di+6],ax
 mov ax,[CHILD_OPCODE]
 mov [cs:di+8],ax
 mov ax,[CHILD_RAW]
 mov [cs:di+10],ax
 mov ax,[CHILD_CLEANUP]
 mov [cs:di+12],ax
 mov ax,[CHILD_CALLS]
 mov [cs:di+14],ax
 mov ax,[CHILD_SCOPE]
 mov [cs:di+16],ax
 mov ax,[CHILD_DISPLAY]
 mov [cs:di+18],ax
 mov ax,[CHILD_BUSY]
 mov [cs:di+20],ax
 mov ax,[CHILD_PROCESS]
 mov [cs:di+22],ax
 mov ax,[CHILD_HEADER]
 mov [cs:di+24],ax
 jmp .done
.allocate:
 cmp word [cs:parent_ds],0
 je .done
 cmp word [cs:alloc_current],0
 jne .done
 mov bx,[cs:parent_ds]
 sub bx,PARENT_DATA_SEG
 add bx,PARENT_RENDER_SEG
 mov es,bx
 mov bx,[es:PARENT_CHILD_DS]
 mov cx,ds
 cmp cx,bx
 jne .done
 mov bx,ss
 cmp bx,cx
 jne .done
 mov di,[cs:alloc_data+4]
 cmp di,16
 jae .done
 inc word [cs:alloc_data+4]
 shl di,1
 shl di,1
 shl di,1
 add di,alloc_records
 mov [cs:alloc_current],di
 mov bp,sp
 mov ax,[ss:bp+14] ; caller BX, requested paragraphs
 mov [cs:di],ax
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
 ; Give the predecessor the original interrupt FLAGS, including caller IF.
 ; The extra saved BP remains below that frame until our final IRET.
 push bp
 mov bp,sp
 push word [ss:bp+6]
 mov bp,[ss:bp]
 call far [cs:old21]
 ; DOS has returned its actual AX/BX/FLAGS. Record without changing them,
 ; then transfer the predecessor flags into the original interrupt frame.
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
 mov bp,sp
 mov di,[cs:alloc_current]
 mov word [cs:alloc_current],0
 mov ax,[ss:bp+16]
 mov [cs:di+2],ax
 mov ax,[ss:bp+14]
 mov [cs:di+4],ax
 mov ax,[ss:bp+18]
 mov [ss:bp+26],ax
 and ax,1
 mov [cs:di+6],ax
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
 add sp,2 ; discard the extra pre-call BP; IRET restores returned flags
 iret
.exec:
 mov bx,ss
 mov cx,ds
 cmp bx,cx
 jne .done
 mov si,dx
 cmp si,0xffb0
 ja .done
 mov cx,70
.scan:
 cmp word [si],0x5341 ; ASPECT.EXE, case/prefix exact owned package
 jne .next
 cmp word [si+2],0x4550
 jne .next
 cmp word [si+4],0x5443
 jne .next
 cmp word [si+6],0x452e
 jne .next
 cmp word [si+8],0x4558
 jne .next
 cmp byte [si+10],0
 jne .next
 mov [cs:parent_ds],ds
 inc word [cs:data+6]
 jmp .done
.next:
 cmp byte [si],0
 je .done
 inc si
 loop .scan
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
 mov [data+8],cs
 mov dx,hook
 mov ax,0x2521
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,hook
 jne failed
 cmp word [es:data],0xae51
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
 mov cx,10+8*26
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,10+8*26
 jne failed
 push ds
 push es
 pop ds
 mov dx,alloc_data
 mov cx,6+16*8
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,6+16*8
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
filename: db 'D:\EXITSTAT.BIN',0
