"""BIOS Escape once after the displayed five-digit KiB count reaches eight.

The original observer looked at only the units digit. Stock helper progress can
jump from7 to15; this observer admits that jump instead of waiting for a8/9.
"""
from zmodem_cancel_watch import SAMPLER as BASE

OLD=''' cmp word [es:3680+70*2],0x1f31
 jb .observed
 cmp word [es:3680+70*2],0x1f39
 ja .observed
'''
NEW=''' mov si,3680+66*2
 mov cx,4
.threshold_prefix:
 mov ax,[es:si]
 cmp ah,0x1f
 jne .observed
 cmp al,'0'
 jb .observed
 cmp al,'9'
 ja .observed
 cmp al,'0'
 jne .threshold_reached
 add si,2
 loop .threshold_prefix
 cmp word [es:3680+70*2],0x1f38
 jb .observed
 cmp word [es:3680+70*2],0x1f39
 ja .observed
.threshold_reached:
'''
assert BASE.count(OLD)==1
SAMPLER=BASE.replace(OLD,NEW)
