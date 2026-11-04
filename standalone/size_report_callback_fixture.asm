; Owned callback ABI boundary for the linked ASPECT size-report check.
; No product instructions are replaced. This is not a child/UART proof.
BITS 16
CPU 8086
ORG 100h
cmp ax,4
je error
cmp ax,2
jne bad
push es
push di
push cs
pop es
mov di,[cs:80h]
cmp di,[cs:82h]
je fail
mov [es:di+1000h],bl
inc word [cs:80h]
xor ax,ax
jmp done
fail:
mov word [cs:84h],9
mov ax,9
done:
pop di
pop es
retf
error:
mov ax,[cs:84h]
retf
bad:
mov ax,10
retf
