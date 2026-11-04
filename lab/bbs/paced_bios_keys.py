"""Test-only paced BIOS keyboard table; self-removes its INT1C hook.

No DOS calls from the callback, serial access, or product-memory writes.
"""
import math


def entries(recipe):
    scans={c:n+i for row,n in [('1234567890-=',2),('qwertyuiop',16),('asdfghjkl',30),('zxcvbnm',44)] for i,c in enumerate(row)}
    scans.update({'!':2,' ':57,'.':52,':':39,'\\':43})
    special={'enter':0x1c0d,'escape':0x011b,'tab':0x0f09,'a-x':0x2d00,'c-y':0x1519}
    pending=1;result=[]
    for token in recipe.split():
        if token.startswith('p') and token[1:].isdigit():
            pending+=math.ceil(int(token[1:])*1193182/65536000)
            continue
        if token in special:word=special[token]
        else:
            c=' ' if token=='space' else token
            assert len(c)==1 and c.lower() in scans,token
            word=scans[c.lower()]<<8|ord(c)
        assert 1<=pending<=65535
        result.append((pending,word));pending=1
    assert result and result[-1][1]==0x2d00
    return result


def source(recipe):
    table=entries(recipe)
    return r'''bits 16
cpu 8086
org 100h
jmp install
old_vector: dd 0
key_cursor: dw keys
ticks: dw 1
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
 dec word [ticks]
 jnz .done
 mov bx,[key_cursor]
 mov cx,[bx+2]
 mov ah,5
 int 16h
 or al,al
 jnz .full
 add word [key_cursor],4
 mov bx,[key_cursor]
 mov ax,[bx]
 or ax,ax
 jz .restore
 mov [ticks],ax
 jmp .done
.full:
 mov word [ticks],1
 jmp .done
.restore:
 ; Restore the vector while interrupts are disabled; call no DOS from ISR.
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[old_vector]
 mov [es:70h],ax
 mov ax,[old_vector+2]
 mov [es:72h],ax
 popf
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
keys:
'''+''.join(f' dw {delay},{word}\n' for delay,word in table)+r''' dw 0,0
resident_end:
install:
 mov ax,351ch
 int 21h
 mov [old_vector],bx
 mov [old_vector+2],es
 mov ax,[keys]
 mov [ticks],ax
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
'''
