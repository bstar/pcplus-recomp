; Original resident9852..9887 strncat,53 exact bytes; independent ndisasm audit.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_append_original
%else
ORG 0x9852
%endif
%include "encodings.inc"
directory_dial_append_original:
 push bp
 mov_load bp,sp
 push di
 push si
 push ds
 pop es
 mov di,[bp+4]
 mov_load dx,di
 xor_load ax,ax
 mov cx,0xffff
 repne scasb
 dec di
 mov_load si,di
 mov di,[bp+6]
 mov_load bx,di
 mov cx,[bp+8]
 repne scasb
 jnz .copy
 inc cx
.copy:
 sub cx,[bp+8]
 neg cx
 mov_load di,si
 mov_load si,bx
 rep movsb
 stosb
 mov_load ax,dx
 pop si
 pop di
 pop bp
 ret
