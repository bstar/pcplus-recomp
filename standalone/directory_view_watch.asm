; Test-only passive directory view observer. Reads video only; no UART/keys.
BITS 16
CPU 8086
ORG 100h
jmp start
old_vector: dw 0,0
sample: dw 0x4456,0,0
%ifdef DIRECTORY_PREVIEW
%define CAPTURE_SIZE 16006
%else
%define CAPTURE_SIZE 12006
%endif
reference_frame: times 4000 db 0
refusal_frame: times 4000 db 0
browser_frame: times 4000 db 0
%ifdef DIRECTORY_PREVIEW
preview_frame: times 4000 db 0
%endif
last_sum: dw 0
stable: dw 0
handler:
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
 push cs
 pop ds
 mov ax,0xb800
 mov es,ax
 inc word [sample+4]
 cmp word [es:4],0x1f50 ; PCPLUS title, row0 col2.
 jne .done
 cmp word [es:6],0x1f43
 jne .done
%ifdef DIRECTORY_PREVIEW
 cmp word [es:3842],0x1f50 ; Preview footer written after proposed fields.
 jne .path
 cmp word [es:484],0x1f53 ; SELECTED ENTRY heading, row3 col2.
 jne .path
 test word [sample+2],16
 jnz .done
 mov di,preview_frame
 call capture
 or word [sample+2],16
 jmp .done
.path:
%endif
 cmp word [es:3842],0x1f45 ; Enter footer in path prompt.
 jne .loading
 or word [sample+2],8
 jmp .done
.loading:
 cmp word [es:804],0x0752 ; Reading directory, row5 col2.
 je .progress
 cmp word [es:804],0x0f43 ; Could not load / Close uncertain notice.
 jne .table
.progress:
 test word [sample+2],4
 jnz .done
 mov di,browser_frame
 call capture
 or word [sample+2],4
 jmp .done
.table:
 cmp word [es:3842],0x1f41 ; Arrows footer written after table fields.
 jne .done
 cmp word [es:484],0x1f4e ; No. column header.
 jne .done
 xor dx,dx
 xor si,si
 mov cx,2000
.sum:
 add dx,[es:si]
 add si,2
 loop .sum
 cmp dx,[last_sum]
 je .same
 mov [last_sum],dx
 mov word [stable],0
 jmp .done
.same:
 inc word [stable]
 cmp word [stable],2
 jb .done
 cmp word [es:656],0x704c ; Selected LoSs entry1, row4 col8.
 jne .last
 test word [sample+2],1
 jnz .done
 mov di,reference_frame
 call capture
 or word [sample+2],1
 jmp .done
.last:
 cmp word [es:644],0x0731 ; Page191..200, unselected row4 begins191.
 jne .done
 cmp word [es:646],0x0739
 jne .done
 cmp word [es:2096],0x7046 ; Selected FINAL200, row13 col8.
 jne .done
 test word [sample+2],2
 jnz .done
 mov di,refusal_frame
 call capture
 or word [sample+2],2

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
 jmp far [cs:old_vector]
capture:
 xor si,si
 mov cx,2000
.copy:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .copy
 ret
resident_end:
start:
 mov ax,0x351c
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x251c
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,0x3100
 int 21h
collect:
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4456
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,CAPTURE_SIZE
.copy:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .copy
 popf
 mov dx,[es:old_vector]
 mov ax,[es:old_vector+2]
 push ds
 mov ds,ax
 mov ax,0x251c
 int 21h
 pop ds
 mov dx,filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,CAPTURE_SIZE
 mov ah,40h
 int 21h
 jc failed
 cmp ax,CAPTURE_SIZE
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 ; Query the actual VGA 8x16 font after restoring the timer vector.
 mov ax,1130h
 mov bh,6
 int 10h
 cmp cx,16
 jne failed
 mov [font_segment],es
 mov [font_offset],bp
 mov dx,fontname
 xor cx,cx
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 push ds
 mov dx,[font_offset]
 mov ds,[font_segment]
 mov cx,4096
 mov ah,40h
 int 21h
 pop ds
 jc failed
 cmp ax,4096
 jne failed
 mov ah,3eh
 int 21h
 jc failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
filename: db 'D:\DIRVIEW.BIN',0
fontname: db 'D:\VGA16.BIN',0
font_segment: dw 0
font_offset: dw 0
buffer: times CAPTURE_SIZE db 0
