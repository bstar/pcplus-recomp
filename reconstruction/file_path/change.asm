; Original 2.01 path/drive helper,75AE..75E7. See docs/FILE_PATH_OWNER.md.
BITS 16
CPU 8086
%ifdef FILE_PATH_OMF
SEGMENT _TEXT public class=CODE use16
global file_path_native_change
%else
ORG 0x75ae
%endif
%include "encodings.inc"
file_path_native_change:
 mov_load bx,sp
 mov bx,[bx+2]
 mov ah,0x3b
 mov_load dx,bx
 int 0x21
 jnc short .selected
 cmp byte [bx+2],0
 jnz short .failed
 cmp byte [bx+1],':'
 jnz short .failed
 cmp byte [bx],'A'
 jl short .failed
.selected:
 cmp byte [bx+1],':'
 jnz short .success
 mov dl,[bx]
 and dl,0xdf
 sub dl,'A'
 mov ah,0x0e
 int 0x21
.success:
 sub_load ax,ax
.return:
 ret 2
.failed:
 mov ax,1
 jmp short .return
