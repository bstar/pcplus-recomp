"""Read-only timer capture of loss/completion notices on every text row.

Keep the existing SNAP installation/collection and hardware snapshots. Capture
only complete notice prefixes, deduplicate all retained rows, and keep scanning
after an old notice so it cannot hide a later completion on another row.
"""
from zmodem_label_watch import SAMPLER as BASE

HEADER, body = BASE.split('handler:\n', 1)
_, TAIL = body.split('resident_end:\n', 1)
SAMPLER = HEADER + r'''handler:
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
 cld
 mov ax,0xb800
 mov es,ax
 mov word [notice_row],0
.row:
 mov di,[notice_row]
 add di,2
 mov si,notice_rx_lost
 call .matches
 jc .observed
 mov si,notice_lost
 call .matches
 jc .observed
 mov si,notice_complete
 call .matches
 jnc .next
.observed:
 inc word [sample+4]
 xor bx,bx
.frame:
 cmp bx,[sample+2]
 jae .capture
 mov ax,160
 mul bx
 mov si,frames
 add si,ax
 mov di,[notice_row]
 mov cx,160
.compare:
 mov al,[es:di]
 cmp [si],al
 jne .different
 inc si
 inc di
 loop .compare
 jmp .next
.different:
 inc bx
 jmp .frame
.capture:
 cmp word [sample+2],16
 jae .next
 mov ax,160
 mul word [sample+2]
 mov si,frames
 add si,ax
 mov di,[notice_row]
 mov cx,160
.copy:
 mov al,[es:di]
 mov [si],al
 inc si
 inc di
 loop .copy
 inc word [sample+2]
.next:
 add word [notice_row],160
 cmp word [notice_row],4000
 jb .row
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
.matches:
 push di
.character:
 lodsb
 or al,al
 jz .found
 cmp al,[es:di]
 jne .missing
 add di,2
 jmp .character
.found:
 pop di
 stc
 ret
.missing:
 pop di
 clc
 ret
notice_row: dw 0
notice_rx_lost: db 'RX carrier lost',0
notice_lost: db 'Carrier lost',0
notice_complete: db 'RX complete',0
resident_end:
''' + TAIL
