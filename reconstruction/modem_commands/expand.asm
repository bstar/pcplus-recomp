; Exact recovered PCPlus2.01 resident4934..498b,87 bytes.
; See docs/MODEM_CONFIGURATION.md for REA provenance and malformed-input limits.
BITS 16
CPU 8086
%ifdef MODEM_COMMANDS_OMF
SEGMENT _TEXT public class=CODE use16
global modem_expand_original
%else
ORG 0x4934
%endif
%include "encodings.inc"
modem_expand_original:
 push bp
 mov_load bp,sp
 sub sp,2
 push di
 push si
 mov si,[bp+4]
 mov di,[bp+6]
.next:
 cmp byte [si],0
 jz .done
 mov al,[si]
 mov [bp-1],al
 cmp al,0x5e
 jnz .emit
 inc si
 mov al,[si]
 cbw
 sub ax,strict word 0x40
 jz .null
 sub ax,strict word 0x1e
 jz .carets
.control:
 mov al,[si]
 and al,0x1f
 mov [bp-1],al
.emit:
 inc si
 mov al,[bp-1]
 inc di
 mov [di-1],al
 jmp short .next
.null:
 mov byte [bp-1],0xff
 jmp short .emit
.carets:
 cmp byte [si+1],0x5e
 jnz .control
 mov byte [bp-1],0x5e
 inc si
 jmp short .emit
.done:
 mov byte [di],0
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
