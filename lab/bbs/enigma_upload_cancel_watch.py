"""Escape once after confirmed TX KiB, then observe only the retry's forms."""
import struct
from enigma_upload_watch import SAMPLER as BASE,events as base_events

SAMPLER=BASE.replace('old_vector: dw 0,0','cancel_gone: dw 0\nretry_seen: dw 0\nold_vector: dw 0,0')
SAMPLER=SAMPLER.replace('cmp word [sample+4],7','cmp word [sample+4],15')
SAMPLER=SAMPLER.replace(' ; The real upload route pauses',r'''
 ; Confirmed progress is visible in the actual TX footer, not inferred from
 ; elapsed time or a product variable. The first source is larger than64KiB.
 cmp word [es:3680+2],0x1f53
 jne .not_sending
 cmp word [es:3680+4],0x1f65
 jne .not_sending
 cmp word [es:3680+18],0x1f5a
 jne .not_sending
 test word [sample+4],8
 jnz .retry_sending
 cmp word [es:3680+70*2],0x1f31
 jb .done
 cmp word [es:3680+70*2],0x1f39
 ja .done
 mov ax,0x40
 mov es,ax
 mov dx,[es:0x50]
 mov di,3
 mov cx,0x011b
 jmp .insert
.retry_sending:
 cmp word [cancel_gone],0
 je .done
 mov word [retry_seen],1
 jmp .done
.not_sending:
 test word [sample+4],8
 jz .done
 mov word [cancel_gone],1
 cmp word [retry_seen],0
 je .done
 ; The real upload route pauses''',1)
SAMPLER=SAMPLER.replace(' inc word [sample+2]\n', ''' inc word [sample+2]
 cmp cx,0x011b
 jne .not_cancel
 or word [sample+4],8
 jmp .tabbed
.not_cancel:
''',1)
assert 'mov cx,0x011b' in SAMPLER and SAMPLER!=BASE


def events(raw):
    assert len(raw)==2566
    magic,count,mask=struct.unpack_from('<HHH',raw)
    assert magic==0x4e5a and 8<=count<=10 and mask==15
    key,cursor,file,tick=struct.unpack_from('<HHHH',raw,6)
    assert key==0x011b and file==3
    remainder=bytearray(raw[:6]+raw[14:]+bytes(8))
    struct.pack_into('<HH',remainder,2,count-1,7)
    tail=base_events(remainder);assert tick<tail[0]['tick']
    return [dict(key='Escape',row=(cursor>>8)+1,column=(cursor&255)+1,file='canceled upload',tick=tick),*tail]
