"""Independent INT1C observer around the unchanged DOS application.

SNAP B records original hardware then installs this timer observer. SNAP S
captures the ordinary screen, collects bounded unique footer frames and removes
the observer before SNAP A verifies original hardware/vector restoration.
No interrupt callback calls DOS or changes product memory.
"""
from test_terminal import SAMPLER as BASE
SAMPLER=BASE.replace(' mov ax,0x4c00\n int 0x21\nfailed:', ''' cmp byte [0x82],'B'
 je install
 cmp byte [0x82],'S'
 je collect
 mov ax,0x4c00
 int 0x21
failed:''')+r'''
old_vector: dw 0,0
sample: dw 0x4e5a,0,0
frames: times 16*160 db 0
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
 mov ax,0xb800
 mov es,ax
 cmp word [es:3840],0x1f52
 jne .done
 cmp word [es:3842],0x1f65
 jne .done
 cmp word [es:3844],0x1f6d
 jne .done
 inc word [sample+4]
 mov bx,[sample+2]
 cmp bx,16
 jae .done
 or bx,bx
 jz .capture
 dec bx
 mov ax,160
 mul bx
 mov si,frames
 add si,ax
 mov di,3840
 mov cx,160
.compare:
 mov al,[es:di]
 cmp [si],al
 jne .capture
 inc si
 inc di
 loop .compare
 jmp .done
.capture:
 mov ax,160
 mul word [sample+2]
 mov si,frames
 add si,ax
 mov di,3840
 mov cx,160
.copy:
 mov al,[es:di]
 mov [si],al
 inc si
 inc di
 loop .copy
 inc word [sample+2]
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
 jmp far [cs:old_vector]
resident_end:
install:
 mov ax,0x351c
 int 0x21
 mov [old_vector],bx
 mov [old_vector+2],es
 mov dx,handler
 mov ax,0x251c
 int 0x21
 mov dx,(resident_end-$$+0x100+15)/16
 mov ax,0x3100
 int 0x21
collect:
 mov ax,0x351c
 int 0x21
 cmp bx,handler
 jne failed
 cmp word [es:sample],0x4e5a
 jne failed
 pushf
 cli
 mov si,sample
 mov di,buffer
 mov cx,2566
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
 int 0x21
 pop ds
 mov dx,label_file
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 mov dx,buffer
 mov cx,2566
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,2566
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc failed
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
 jmp failed
label_file: db 'D:\LABELS.BIN',0
buffer: times 2566 db 0
'''
assert SAMPLER != BASE
