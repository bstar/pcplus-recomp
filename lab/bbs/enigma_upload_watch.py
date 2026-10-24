"""Bounded BIOS-key driver for the two visible synthetic upload detail forms.

Observe VGA title/text and the BIOS cursor only. Never read product variables,
call DOS inside the timer, consume UART bytes or invent protocol replies.
The existing sampler collects/removes this observer before hardware comparison.
"""
import struct
from zmodem_label_watch import SAMPLER as BASE

START=BASE.index('old_vector: dw 0,0')
END=BASE.index('resident_end:')
SAMPLER=BASE[:START]+r'''
old_vector: dw 0,0
sample: dw 0x4e5a,0,0
frames: times 2560 db 0
ticks: dw 0
cooldown: dw 0
stable: dw 0
previous_cursor: dw 0xffff
previous_file: dw 0
title: db 'UPLOAD DETAILS - ',0
binary_name: db 'PCUP01.BIN',0
empty_name: db 'EMPTY.BIN',0
button: db 'ONTINUE',0
pause_text: db '>> smash your keyboard <<',0
checker_title: db 'UPLOAD CHECKER',0
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
 cld
 inc word [ticks]
 cmp word [sample+2],12
 jae .done
 cmp word [sample+4],7
 je .done
 cmp word [cooldown],0
 je .screen
 dec word [cooldown]
 jmp .done
.screen:
 mov ax,0xb800
 mov es,ax
 ; The real upload route pauses after scanning, before the detail forms.
 test word [sample+4],4
 jnz .details
 mov si,pause_text
 mov di,24*160
 call compare_text
 jnc .pause_seen
 mov si,pause_text
 mov di,23*160
 call compare_text
 jnc .pause_seen
 mov si,pause_text
 mov di,22*160
 call compare_text
 jc .details
.pause_seen:
 ; Login screens use the same pause prompt. Only acknowledge the checker.
 xor di,di
 mov cx,1988
.find_checker:
 cmp byte [es:di],'U'
 jne .advance
 push cx
 push di
 mov si,checker_title
 call compare_text
 pop di
 pop cx
 jnc .paused_upload
.advance:
 add di,2
 loop .find_checker
 jmp .details
.paused_upload:
 mov ax,0x40
 mov es,ax
 mov dx,[es:0x50]
 xor di,di
 mov cx,0x1c0d
 jmp .insert
.details:
 test word [sample+4],4
 jz .done
 mov si,title
 mov di,320+7*2
 call compare_text
 jc .reset
 mov bx,1
 mov si,binary_name
 cmp byte [es:320+24*2],'P'
 je .filename
 mov bx,2
 mov si,empty_name
.filename:
 mov di,320+24*2
 call compare_text
 jc .reset
 test [sample+4],bx
 jnz .reset
 ; Require the actual Continue text, not a processing screen with a filename.
 mov si,button
 mov di,13*160+55*2
 call compare_text
 jc .reset
 mov ax,0x40
 mov es,ax
 mov dx,[es:0x50]
 ; Recognized focus positions in this exact owned form/theme.
 cmp dh,5
 je .field
 cmp dl,51
 jb .reset
 cmp dl,70
 ja .reset
 cmp dh,8
 je .field
 cmp dh,13
 jne .reset
.field:
 cmp dl,5
 jb .reset
 cmp dl,75
 ja .reset
 cmp [previous_cursor],dx
 jne .changed
 cmp [previous_file],bx
 jne .changed
 inc word [stable]
 cmp word [stable],36
 jb .done
 mov di,bx
 mov cx,0x0f09
 cmp dh,13
 jne .insert
 mov cx,0x1c0d
.insert:
 push cx
 push dx
 push di
 push ds
 push es
 mov ah,5
 int 0x16
 pop es
 pop ds
 pop di
 pop dx
 pop cx
 or al,al
 jnz .done
 mov bx,[sample+2]
 shl bx,1
 shl bx,1
 shl bx,1
 mov [frames+bx],cx
 mov [frames+bx+2],dx
 mov [frames+bx+4],di
 mov ax,[ticks]
 mov [frames+bx+6],ax
 inc word [sample+2]
 cmp cx,0x1c0d
 jne .tabbed
 or di,di
 jnz .submitted
 or word [sample+4],4
 jmp .tabbed
.submitted:
 or [sample+4],di
.tabbed:
 mov word [cooldown],36
 jmp .reset
.changed:
 mov [previous_cursor],dx
 mov [previous_file],bx
.reset:
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
 jmp far [cs:old_vector]
compare_text:
 lodsb
 or al,al
 jz .yes
 ; The owned button changes continue/cONTINUE with focus.
 mov ah,[es:di]
 or al,0x20
 or ah,0x20
 cmp al,ah
 jne .no
 add di,2
 jmp compare_text
.no:
 stc
 ret
.yes:
 clc
 ret
'''+BASE[END:]


def compact_sampler():
    """Keep exactly the twelve bounded eight-byte events in conventional RAM."""
    assert SAMPLER.count('frames: times 2560 db 0')==1
    assert SAMPLER.count('2566')==4
    return SAMPLER.replace('frames: times 2560 db 0','frames: times 96 db 0').replace('2566','102')


def compact_events(raw):
    assert len(raw)==102
    return events(raw+bytes(2566-102))


def events(raw):
    assert len(raw)==2566
    magic,count,submitted=struct.unpack_from('<HHH',raw)
    assert magic==0x4e5a and submitted==7 and 7<=count<=9
    rows=[];by_file={1:[],2:[]}
    for i in range(count):
        key,cursor,file,tick=struct.unpack_from('<HHHH',raw,6+i*8)
        row,col=cursor>>8,cursor&255
        if i==0:
            assert file==0 and key==0x1c0d
            rows.append(dict(key='Enter',row=row+1,column=col+1,file='scan pause',tick=tick))
            continue
        field=4 if row==13 else 3 if row==8 else 2 if row==5 and col>=51 else 1 if row==5 else 0
        assert file in by_file and field and key==(0x1c0d if field==4 else 0x0f09)
        by_file[file].append(field)
        rows.append(dict(key='Enter' if field==4 else 'Tab',row=row+1,column=col+1,file='PCUP01.BIN' if file==1 else 'EMPTY.BIN',tick=tick))
    assert all(fields in ([1,2,3,4],[2,3,4]) for fields in by_file.values()),by_file
    assert all(b['tick']>a['tick'] for a,b in zip(rows,rows[1:]))
    return rows
