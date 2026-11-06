; Passive INT1C observer paired with the owned BUSYW INT16 observer.
; Reads actual parent PROGRAM snapshot, native state and loaded Chat image.
; Never calls DOS/BIOS in the ISR or writes parent/video/BIOS state.
BITS 16
CPU 8086
ORG 100h
jmp start
old: dd 0
; magic,phase,ticks,rows,before xy/shape,Help xy/shape,after xy/shape,
; parentDS,module-before/Help/after,Help owner/parser/wait/active/kind,
; after owner/parser/wait,Help/after exact-image equality,busy flags.
sample: dw 0x4842,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
frames: times 24000 db 0xa5
busy_segment: dw 0
busy_image: dw 0
last: dw 0
stable: dw 0

; AX=parentDS, CF=0, after checking the auxiliary observer's public header.
parent:
 xor ax,ax
 mov es,ax
 mov ax,[es:0x5a]
 mov es,ax
 cmp word [es:0x103],0x5742
 jne .bad
 cmp word [es:0x105],0x0032
 jne .bad
 mov [busy_segment],ax
 cmp word [es:0x10b],IMAGE_BYTES
 jne .bad
 mov bx,[es:0x109]
 mov [busy_image],bx
 mov bx,[es:0x10d]
 mov dx,[es:bx+2]
 mov [sample+48],dx
 mov bx,[es:0x107]
 mov ax,[es:bx]
 or ax,ax
 jz .bad
 clc
 ret
.bad:
 stc
 ret

; AX=1 only for exact equality to the pre-wait image held by BUSYW.
image_equal:
 push ds
 mov ax,[sample+20]
 add ax,FROZEN_DELTA
 mov es,ax
 mov si,[busy_image]
 mov ax,[busy_segment]
 mov ds,ax
 xor di,di
 mov cx,IMAGE_BYTES/2
 cld
 repe cmpsw
 mov ax,0
 jne .done
 inc ax
.done:
 pop ds
 ret

handler:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 push cs
 pop ds
 inc word [sample+4]
 cmp word [sample+2],3
 jae .done
 call parent
 jc .done
 cmp word [sample+2],0
 jne .return_candidate
 mov [sample+20],ax
 add ax,FROZEN_DELTA
 mov [sample+22],ax
 mov ax,0xb800
 mov es,ax
 cmp byte [es:2],'C'
 jne .done
 cmp byte [es:4],'h'
 jne .done
 cmp byte [es:6],'a'
 jne .done
 jmp .candidate
.return_candidate:
 cmp ax,[sample+20]
 jne .done
 mov es,ax
 cmp word [es:ACTIVE_OFF],0
 jne .done
 mov dx,[es:CURSOR_OFF]
 cmp dx,[sample+8]
 jne .done
 mov ax,0xb800
 mov es,ax
 cmp byte [es:72],'R'
 jne .done
 cmp byte [es:74],'E'
 jne .done
 cmp byte [es:76],'M'
 jne .done
.candidate:
 mov ax,0x40
 mov es,ax
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 cmp ax,50
 ja .done
 cmp ax,25
 jb .done
 mov [sample+6],ax
 mov bx,80
 mul bx
 mov cx,ax
 mov ax,0xb800
 mov es,ax
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
 cmp word [sample+2],0
 jne .after
 mov ax,[sample+20]
 mov es,ax
 mov ax,[es:CURSOR_OFF]
 mov [sample+8],ax
 mov ax,[es:SHAPE_OFF]
 mov [sample+10],ax
 mov ax,[es:OWNER_OFF]
 mov [sample+28],ax
 mov ax,[es:PARSER_OFF]
 mov [sample+30],ax
 mov ax,[es:WAIT_OFF]
 mov [sample+32],ax
 mov ax,[es:ACTIVE_OFF]
 mov [sample+34],ax
 mov ax,[es:KIND_OFF]
 mov [sample+36],ax
 mov ax,[sample+20]
 add ax,FROZEN_DELTA
 mov [sample+24],ax
 call image_equal
 mov [sample+44],ax
 ; Capture the actual pre-child PROGRAM snapshot, not a recreated Chat UI.
 mov ax,[sample+20]
 add ax,PROGRAM_DELTA
 mov es,ax
 push ds
 push es
 pop ds
 push cs
 pop es
 mov si,PROGRAM_OFFSET
 mov di,frames
 mov ax,[cs:sample+6]
 mov bx,80
 mul bx
 mov cx,ax
 cld
 rep movsw
 pop ds
 mov di,frames+8000
 mov bx,12
 mov word [sample+2],2
 jmp .visible
.after:
 mov ax,[sample+20]
 mov es,ax
 mov ax,[es:OWNER_OFF]
 mov [sample+38],ax
 mov ax,[es:PARSER_OFF]
 mov [sample+40],ax
 mov ax,[es:WAIT_OFF]
 mov [sample+42],ax
 mov ax,[sample+20]
 add ax,FROZEN_DELTA
 mov [sample+26],ax
 call image_equal
 mov [sample+46],ax
 mov di,frames+16000
 mov bx,16
 mov word [sample+2],3
.visible:
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [sample+bx],ax
 mov ax,[es:0x60]
 mov [sample+bx+2],ax
 mov ax,[sample+6]
 mov bx,80
 mul bx
 mov cx,ax
 mov ax,0xb800
 mov es,ax
 xor si,si
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 mov word [stable],0
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
 jmp far [cs:old]
resident_end:
start:
 mov ax,0x351c
 int 0x21
 cmp byte [0x82],'T'
 jne collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4842
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,24050
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov dx,[es:old]
 mov ax,[es:old+2]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 0x21
 pop ds
 popf
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,24050
 mov ah,0x40
 int 0x21
 jc failed
 cmp ax,24050
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
name: db 'HELPLIFE.BIN',0
buffer: resb 24050
