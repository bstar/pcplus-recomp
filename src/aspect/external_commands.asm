; Exact native DOS/RUN parser and SHELL frontend. The application executor
; boundary is deliberately unresolved until display/UART/process ownership is
; integrated. Do not add these handlers to the production dispatch table yet.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_EXTERNAL_FLAT
%if ASPECT_EXTERNAL_UNIT=1
ORG 0xf1fc
%elif ASPECT_EXTERNAL_UNIT=2
ORG 0xf20b
%elif ASPECT_EXTERNAL_UNIT=3
ORG 0xdc34
%endif
%define aspect_string_read 0xdf04
%define aspect_string_option_flag 0xe0e4
%define aspect_dispatch_read 0x4cb4
%define aspect_string_compare_result 0xd124
%define program_strcpy 0x8268
%define program_strchr 0x8c2a
%define external_execute 0x433d
%define external_getenv 0x8e12
%define external_ctype 0x7caf
%define external_comspec 0x318c
%if ASPECT_EXTERNAL_UNIT!=2
%define external_common 0xf20b
%endif
%else
%define ASPECT_EXTERNAL_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_external_dos,aspect_external_run,aspect_external_shell
extern aspect_string_read,aspect_string_option_flag,aspect_dispatch_read
extern aspect_string_compare_result,program_strcpy,program_strchr
extern _runtime_external_execute,_runtime_environment_get
%define external_execute _runtime_external_execute
%define external_getenv _runtime_environment_get
%endif
%if ASPECT_EXTERNAL_UNIT=0 || ASPECT_EXTERNAL_UNIT=1
aspect_external_dos:
 sub_load ax,ax
 push ax
 call external_common
 ret
aspect_external_run:
 mov ax,1
 push ax
 call external_common
 ret
%endif
%if ASPECT_EXTERNAL_UNIT=0 || ASPECT_EXTERNAL_UNIT=2
external_common:
 push bp
 mov_load bp,sp
 sub sp,byte 0x58
 push si
 mov word [bp-4],0
 call aspect_string_read
 push ax
 lea si,[bp-0x56]
 push si
 call program_strcpy
 pop bx
 pop bx
 cmp word [bp+4],byte 0
 jnz .trim_next
.no_arguments:
 mov word [bp-2],0
.option:
 call aspect_string_option_flag
 or_load ax,ax
 jz .execute
 call aspect_dispatch_read
 mov [bp-4],ax
.execute:
 mov [bp-0x58],si
 cmp word [bp-4],byte 0x25
 jz .noclear
 mov ax,1
 jmp short .save
.trim:
 inc si
.trim_next:
 mov bl,[si]
 sub_load bh,bh
 test byte [bx+external_ctype],8
 jnz .trim
 mov ax,0x20
 push ax
 push si
 call program_strchr
 pop bx
 pop bx
 mov [bp-2],ax
 or_load ax,ax
 jz .no_arguments
 cmp_load ax,si
 jz .no_arguments
 mov_load bx,ax
 inc word [bp-2]
 mov byte [bx],0
 jmp short .option
.noclear:
 sub_load ax,ax
.save:
 push ax
 cmp word [bp-4],byte 0x36
 jnz .no_wait
 mov ax,1
 jmp short .wait
.no_wait:
 sub_load ax,ax
.wait:
 push ax
 cmp word [bp+4],byte 1
 sbb_load ax,ax
 neg ax
 push ax
 push word [bp-2]
 push si
 call external_execute
 add sp,byte 10
 mov [aspect_string_compare_result],ax
 pop si
 mov_load sp,bp
 pop bp
 ret 2
%endif
%if ASPECT_EXTERNAL_UNIT=0 || ASPECT_EXTERNAL_UNIT=3
aspect_external_shell:
 mov ax,1
 push ax
 sub_load ax,ax
 push ax
 push ax
 push ax
 mov ax,external_comspec
 push ax
 call external_getenv
 pop bx
 push ax
 call external_execute
 add sp,byte 10
 ret
%endif
%ifndef ASPECT_EXTERNAL_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
external_comspec: db 'COMSPEC',0
; Only the whitespace bit is observed by the exact native parser.
external_ctype:
%assign external_byte 0
%rep 256
%if external_byte=9 || external_byte=10 || external_byte=11 || external_byte=12 || external_byte=13 || external_byte=32
 db 8
%else
 db 0
%endif
%assign external_byte external_byte+1
%endrep
%endif
