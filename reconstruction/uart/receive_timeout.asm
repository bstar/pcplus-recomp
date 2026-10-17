; REA function 0x15ca0: 36 BIOS clock changes before receive timeout.
; Ghidra pseudocode incorrectly removed the timer path as unreachable.
; Keep the observed assembly: BIOS memory changes asynchronously.
BITS 16
CPU 8086
ORG 0x5ca0

    cmp word [0x8e20], byte 0
    jnz short .read
    mov dx, 36
    sti
    db 0x33, 0xc9          ; XOR CX, CX; original load-form encoding
    mov es, cx
    mov bx, 0x46c
.tick:
    mov ax, [es:bx]
.wait:
    cmp word [0x8e20], byte 0
    jnz short .read
    cmp ax, [es:bx]
    jz short .wait
    inc cx
    db 0x3b, 0xca          ; CMP CX, DX; original load-form encoding
    jb short .tick
    mov ax, 0xffff
    ret
.read:
    call 0xaa65
    ret
