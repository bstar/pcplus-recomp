; CONFIG_CODE-local near DOS probe. Never read, create or write the resource.
%ifdef DIRECTORY_KEY_BINDINGS
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
global _directory_binding_probe
_directory_binding_probe:
 push bp
 mov bp,sp
 push bx
 mov dx,[bp+4]
 mov ax,0x3d00
 int 0x21
 jc .done
 mov bx,ax
 mov ah,0x3e
 int 0x21
 jc .done
 xor ax,ax
.done:
 pop bx
 pop bp
 ret
%endif
