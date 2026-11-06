; Exact native6C4A BIOS write-one-character wrapper; caller supplies attribute
; and character words. RET4. BIOS09 writes without advancing the cursor.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0x6c4a
%else
SEGMENT _TEXT public class=CODE use16
global chat_bios_character
%endif
%include "encodings.inc"
chat_bios_character:
 mov_load bx,sp
 mov ax,[bx+4]
 mov bx,[bx+2]
 mov cx,1
 mov ah,9
 push bp
 int 0x10
 pop bp
 ret 4
