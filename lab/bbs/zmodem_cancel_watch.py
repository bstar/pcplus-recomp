"""Independent timer observer presses Escape once after visible received KiB.

Uses the existing BIOS keystroke API, never product data or a protocol reply.
The high bit of the observer's tick word records successful BIOS insertion.
"""
from zmodem_label_watch import SAMPLER as BASE

SAMPLER=BASE.replace('old_vector: dw 0,0','injected: dw 0\nold_vector: dw 0,0')
SAMPLER=SAMPLER.replace(' inc word [sample+4]\n',r'''
 inc word [sample+4]
 cmp word [injected],0
 jne .observed
 ; Progress is drawn at row23 columns66..70, with VGA attribute1f.
 ; The stored fixture takes many seconds; one KiB is safely before EOF.
 cmp word [es:3680+70*2],0x1f31
 jb .observed
 cmp word [es:3680+70*2],0x1f39
 ja .observed
 push ds
 push es
 mov cx,0x011b
 mov ah,5
 int 0x16
 pop es
 pop ds
 or al,al
 jnz .observed
 mov word [injected],1
 or word [sample+4],0x8000
.observed:
''')
assert SAMPLER != BASE and 'mov cx,0x011b' in SAMPLER
