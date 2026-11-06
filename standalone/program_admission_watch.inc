; Optional read-only timer observer, appended to the existing UMB BBS observer.
; Samples parent results through its live IRQ identity; no DOS in interrupt.
admission_old: dd 0
admission_old21: dd 0
admission_data: dw 0xad41,1,0,0,0,0,0,0,0,0,0,0,0,0
admission_open: dw 0,0,0,0
admission_hook21:
 pushf
 cmp ah,3dh
 je .inspect
 cmp ax,6c00h
 jne .chain
.inspect:
 push ax
 push cx
 push si
 cmp ah,3dh
 jne .filename_ready
 mov si,dx
.filename_ready:
 cmp si,0xffc0
 ja .unmatched
 mov cx,56
.scan:
 cmp byte [si],0
 je .unmatched
 cmp word [si],5953h ; SYNC.ASX, owned fixture only.
 jne .next
 cmp word [si+2],434eh
 jne .next
 cmp word [si+4],412eh
 jne .next
 cmp word [si+6],5853h
 jne .next
 cmp byte [si+8],0
 je .matched
.next:
 inc si
 loop .scan
.unmatched:
 pop si
 pop cx
 pop ax
.chain:
 popf
 jmp far [cs:admission_old21]
.matched:
 inc word [cs:admission_open]
 mov [cs:admission_open+6],ax
 pop si
 pop cx
 pop ax
 popf
 push bp
 mov bp,sp
 pushf
 call far [cs:admission_old21]
 mov [cs:admission_open+4],ax
 pushf
 pop word [cs:admission_open+2]
 push ax
 mov ax,[cs:admission_open+2]
 and ax,1
 and word [ss:bp+6],0xfffe
 or [ss:bp+6],ax
 pop ax
 pop bp
 iret
admission_sample:
 pushf
 save
 inc word [admission_data+4]
 xor ax,ax
 mov es,ax
 cmp word [es:13*4],ADMISSION_ISR_OFFSET
 jne .done
 mov bx,[es:13*4+2]
 sub bx,ADMISSION_ISR_SEGMENT
 jc .done
 mov ax,bx
 add ax,ADMISSION_DATA_SEGMENT
 mov es,ax
 mov ax,[es:ADMISSION_PSP]
 add ax,16
 cmp ax,bx
 jne .done
 inc word [admission_data+6]
 cmp word [es:ADMISSION_PROGRAM_KIND],4
 jne .done
 inc word [admission_data+8]
 mov ax,[es:ADMISSION_PROGRAM_STATUS]
 cmp ax,5
 jne .done
 mov [admission_data+10],ax
 mov ax,[es:ADMISSION_PROCESS_STATUS]
 mov [admission_data+12],ax
 mov ax,[es:ADMISSION_DOS_ERROR]
 mov [admission_data+14],ax
 mov ax,[es:ADMISSION_CHILD_STATUS]
 mov [admission_data+16],ax
 mov ax,[es:ADMISSION_KEEP]
 mov [admission_data+18],ax
 mov si,ADMISSION_RESULT
 mov di,admission_data+20
 mov cx,4
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
.done:
 restore
 popf
 jmp far [cs:admission_old]
admission_install:
 mov ax,3521h
 int 21h
 mov [admission_old21],bx
 mov [admission_old21+2],es
 mov dx,admission_hook21
 mov ax,2521h
 int 21h
 mov ax,351ch
 int 21h
 mov [admission_old],bx
 mov [admission_old+2],es
 mov dx,admission_sample
 mov ax,251ch
 int 21h
 ret
admission_collect:
 ; Mainline collection after the parent exits; BIOS multiplex query returned
 ; the existing observer's report at ES:DI. New collector uses that segment.
 push ds
 mov ax,es
 mov ds,ax
 ; These two extra vectors belong only to this diagnostic. Retire them before
 ; collecting the report so the final hardware witness sees the original IVT.
 push ds
 mov dx,[admission_old21]
 mov ax,[admission_old21+2]
 mov ds,ax
 mov ax,2521h
 int 21h
 pop ds
 push ds
 mov dx,[admission_old]
 mov ax,[admission_old+2]
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,admission_name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc .done
 mov bx,ax
 mov dx,admission_data
 mov cx,36
 mov ah,40h
 int 21h
 mov ah,3eh
 int 21h
.done:
 pop ds
 ret
admission_name: db 'D:\ADMIT.BIN',0
