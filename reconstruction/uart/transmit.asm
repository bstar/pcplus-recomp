; REA function 0x1ad93; sends CL after UART LSR bit 5 becomes set.
; Original file offset 0xbf93; 17 bytes. No behavioral changes.
BITS 16
CPU 8086
ORG 0xad93

    mov dx, [0x900a]       ; UART base + 5, initialized by REA function 0x10366
.wait:
    in al, dx
    and al, 0x20
    jz short .wait
    db 0x8a, 0xc1          ; MOV AL, CL; preserve the original load-form encoding
    mov dx, [0x9012]       ; UART base, transmit holding register
    out dx, al
    ret
