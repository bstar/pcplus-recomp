; Exact PCPlus 2.01 XLT file operations and identity reset.
; Original unchecked CRT behavior is retained here, not a maintained loader.
BITS 16
CPU 8086
%ifdef TRANSLATION_OMF
SEGMENT _TEXT public class=CODE use16
global translation_save_original,translation_load_original,translation_identity_original
extern translation_filename,translation_file,translation_table
extern translation_mode_write,translation_mode_read
extern translation_resolve,translation_fopen,translation_fwrite,translation_fread,translation_fclose
%define short
%else
ORG 0x35a6
%define translation_filename 0x324e
%define translation_file 0x8fec
%define translation_table 0xd00a
%define translation_mode_write 0x4720
%define translation_mode_read 0x4723
%define translation_resolve 0x353d
%define translation_fopen 0x841a
%define translation_fwrite 0x86ac
%define translation_fread 0x845a
%define translation_fclose 0x8318
%endif
%include "encodings.inc"
translation_save_original:
 mov ax,translation_mode_write
 push ax
 push word [translation_filename]
 call translation_resolve
 pop bx
 push ax
 call translation_fopen
 pop bx
 pop bx
 mov [translation_file],ax
 push ax
 mov ax,256
 push ax
 mov ax,1
 push ax
 mov ax,translation_table
 push ax
 call translation_fwrite
 add sp,8
 push word [translation_file]
 call translation_fclose
 pop bx
 ret
translation_load_original:
 mov ax,translation_mode_read
 push ax
 push word [translation_filename]
 call translation_resolve
 pop bx
 push ax
 call translation_fopen
 pop bx
 pop bx
 mov [translation_file],ax
 push ax
 mov ax,256
 push ax
 mov ax,1
 push ax
 mov ax,translation_table
 push ax
 call translation_fread
 add sp,8
 push word [translation_file]
 call translation_fclose
 pop bx
 ret
translation_identity_original:
 sub_load bx,bx
.next:
 mov [translation_table+bx],bl
 inc bx
 cmp bx,256
 jl short .next
 ret
