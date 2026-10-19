; Exact native DOS path helpers. CHDIR RET2, other public entries cdecl.
; AH39/41 share the real recovered CRT result/error mapper; AH3A returns raw
; DOS AX on carry. Drive-only CHDIR fallback and its unverified select remain
; native behavior. No wildcard expansion or synthesized comparison update.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_PATH_SERVICE_FLAT
%if ASPECT_PATH_SERVICE_UNIT=1
ORG 0x75ae
%elif ASPECT_PATH_SERVICE_UNIT=2
ORG 0x9c40
%elif ASPECT_PATH_SERVICE_UNIT=3
ORG 0x9c4c
%elif ASPECT_PATH_SERVICE_UNIT=4
ORG 0x9086
%elif ASPECT_PATH_SERVICE_UNIT=5
ORG 0xf2c6
%endif
%define program_access_result 0x9420
%if ASPECT_PATH_SERVICE_UNIT!=3
%define aspect_path_dos_path 0x9c4c
%endif
%else
%define ASPECT_PATH_SERVICE_UNIT 0
%define short
SEGMENT _TEXT public class=CODE use16
global aspect_path_change_directory,aspect_path_make_directory,aspect_path_remove_directory,aspect_path_unlink
extern program_access_result
%endif
%if ASPECT_PATH_SERVICE_UNIT=0 || ASPECT_PATH_SERVICE_UNIT=1
aspect_path_change_directory:
 mov_load bx,sp
 mov bx,[bx+2]
 mov ah,0x3b
 mov_load dx,bx
 int 0x21
 jnc .selected
 cmp byte [bx+2],0
 jne .failed
 cmp byte [bx+1],0x3a
 jne .failed
 cmp byte [bx],0x41
 jl .failed
.selected:
 cmp byte [bx+1],0x3a
 jne .okay
 mov dl,[bx]
 and dl,0xdf
 sub dl,0x41
 mov ah,0x0e
 int 0x21
.okay:
 sub_load ax,ax
.done:
 ret 2
.failed:
 mov ax,1
 jmp short .done
%endif
%if ASPECT_PATH_SERVICE_UNIT=0 || ASPECT_PATH_SERVICE_UNIT=2
aspect_path_make_directory:
 push bp
 mov_load bp,sp
 mov ah,0x39
 jmp short aspect_path_dos_path
%endif
%if ASPECT_PATH_SERVICE_UNIT=0 || ASPECT_PATH_SERVICE_UNIT=3
aspect_path_dos_path:
 mov dx,[bp+4]
 int 0x21
 jmp near program_access_result
%endif
%if ASPECT_PATH_SERVICE_UNIT=0 || ASPECT_PATH_SERVICE_UNIT=4
aspect_path_unlink:
 push bp
 mov_load bp,sp
 mov dx,[bp+4]
 mov ah,0x41
 int 0x21
 jmp near program_access_result
%endif
%if ASPECT_PATH_SERVICE_UNIT=0 || ASPECT_PATH_SERVICE_UNIT=5
aspect_path_remove_directory:
 mov_load bx,sp
 mov ah,0x3a
 mov dx,[bx+2]
 int 0x21
 jc .done
 xor_load ax,ax
.done:
 ret
%endif
