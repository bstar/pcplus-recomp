; Exact PCPlus2.01 GETENV/PUTENV, bounded result copy and near CRT services.
; Runtime ownership adapts PUTENV's borrowed argument, not its case/status rules.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_ENVIRONMENT_FLAT
%if ASPECT_ENVIRONMENT_UNIT=1
ORG 0xe76b
%elif ASPECT_ENVIRONMENT_UNIT=2
ORG 0xe823
%elif ASPECT_ENVIRONMENT_UNIT=3
ORG 0xf0b5
%elif ASPECT_ENVIRONMENT_UNIT=4
ORG 0x8e12
%elif ASPECT_ENVIRONMENT_UNIT=5
ORG 0x9600
%elif ASPECT_ENVIRONMENT_UNIT=6
ORG 0x96d0
%endif
%define aspect_string_read 0xdf04
%define aspect_string_read_destination 0xdf0b
%define aspect_string_flush 0xe0a4
%define aspect_string_error 0x4efb
%define aspect_string_compare_result 0xd124
%define program_strcpy 0x8268
%define aspect_string_upper 0x9128
%define aspect_string_strlen 0x8d18
%define program_strncmp 0x9c06
%define erase_move_bytes 0x85b4
%define environment_buffer 0x4b04
%define environment_table 0x7b43
%define environment_empty 0x4942
%define environment_realloc 0xa7ca
%if ASPECT_ENVIRONMENT_UNIT!=3
%define environment_copy_result 0xf0b5
%endif
%if ASPECT_ENVIRONMENT_UNIT!=4
%define environment_get_native 0x8e12
%endif
%if ASPECT_ENVIRONMENT_UNIT!=5
%define environment_put_native 0x9600
%endif
%if ASPECT_ENVIRONMENT_UNIT!=6
%define environment_find_native 0x96d0
%endif
%define environment_get environment_get_native
%define environment_put environment_put_native
%else
%define ASPECT_ENVIRONMENT_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_environment_get,aspect_environment_put
global _environment_get_native,_environment_put_native
extern aspect_string_read,aspect_string_read_destination,aspect_string_flush
extern aspect_string_error,aspect_string_compare_result,program_strcpy
extern aspect_string_upper,aspect_string_strlen,program_strncmp,erase_move_bytes
extern _runtime_environment_get,_runtime_environment_put
extern _runtime_environment_table,_runtime_environment_realloc
%define environment_table _runtime_environment_table
%define environment_realloc _runtime_environment_realloc
%define environment_get _runtime_environment_get
%ifdef ASPECT_ENVIRONMENT_UNOWNED
%define environment_put environment_put_native
%else
%define environment_put _runtime_environment_put
%endif
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=1
aspect_environment_get:
 push bp
 mov_load bp,sp
 sub sp,byte 0x52
 call aspect_string_read
 push ax
 lea ax,[bp-0x52]
 push ax
 call program_strcpy
 pop bx
 pop bx
 lea ax,[bp-0x52]
 push ax
 call aspect_string_upper
 pop bx
 call aspect_string_read_destination
 push ax
 lea ax,[bp-0x52]
 push ax
 call environment_get
 pop bx
 push ax
 call environment_copy_result
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=2
aspect_environment_put:
 call aspect_string_read
 push ax
 push word [environment_buffer]
 call program_strcpy
 pop bx
 pop bx
 push word [environment_buffer]
 call aspect_string_upper
 pop bx
 push word [environment_buffer]
 call environment_put
 pop bx
 mov [aspect_string_compare_result],ax
 ret
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=3
environment_copy_result:
 push bp
 mov_load bp,sp
 push si
 cmp word [bp+4],byte 0
 jz .missing
 push word [bp+4]
 call aspect_string_strlen
 pop bx
 mov_load si,ax
 cmp si,byte 0x50
 jbe .copy
 mov ax,3
 push ax
 call aspect_string_error
 mov si,0x50
.copy:
 push si
 push word [bp+4]
 push word [bp+6]
 call erase_move_bytes
 add sp,byte 6
 mov bx,[bp+6]
 mov byte [bx+si],0
 jmp short .done
.missing:
 mov ax,environment_empty
 push ax
 push word [bp+6]
 call program_strcpy
 pop bx
 pop bx
.done:
 call aspect_string_flush
 pop si
 mov_load sp,bp
 pop bp
 ret 4
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=4
environment_get_native:
%ifndef ASPECT_ENVIRONMENT_FLAT
_environment_get_native:
%endif
 push bp
 mov_load bp,sp
 push di
 push si
 mov si,[environment_table]
 or_load si,si
 jz .missing
 cmp word [bp+4],byte 0
 jz .missing
 push word [bp+4]
 call aspect_string_strlen
 add sp,byte 2
 mov_load di,ax
 jmp short .next
.entry:
 push word [si]
 call aspect_string_strlen
 add sp,byte 2
 cmp_load ax,di
 jle .advance
 mov bx,[si]
 cmp byte [bx+di],0x3d
 jnz .advance
 push di
 push word [bp+4]
 push bx
 call program_strncmp
 add sp,byte 6
 or_load ax,ax
 jnz .advance
 mov ax,[si]
 add_load ax,di
 inc ax
 jmp short .done
 nop
.advance:
 inc si
 inc si
.next:
 cmp word [si],byte 0
 jnz .entry
.missing:
 sub_load ax,ax
.done:
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=5
environment_put_native:
%ifndef ASPECT_ENVIRONMENT_FLAT
_environment_put_native:
%endif
 push bp
 mov_load bp,sp
 sub sp,byte 4
 push di
 push si
 cmp word [bp+4],byte 0
 jnz .input
.failed:
 mov ax,0xffff
 jmp near .done
.input:
 mov ax,[bp+4]
 mov [bp-2],ax
 jmp short .scan
.advance:
 inc word [bp-2]
.scan:
 mov bx,[bp-2]
 cmp byte [bx],0x3d
 jz .found
 cmp byte [bx],0
 jnz .advance
 jmp short .failed
.found:
 cmp byte [bx+1],1
 sbb_load ax,ax
 neg ax
 mov [bp-4],ax
 mov si,[environment_table]
 sub bx,[bp+4]
 push bx
 push word [bp+4]
 call environment_find_native
 add sp,byte 4
 mov_load di,ax
 or_load di,di
 jl .append
 cmp word [si],byte 0
 jz .append
 cmp word [bp-4],byte 0
 jz .replace
 jmp short .shift_next
 nop
.shift:
 add_load bx,si
 mov ax,[bx+2]
 mov [bx],ax
 inc di
.shift_next:
 mov_load bx,di
 shl bx,1
 cmp word [bx+si],byte 0
 jnz .shift
 mov_load ax,di
 shl ax,1
 push ax
 push si
 call environment_realloc
 add sp,byte 4
 mov_load si,ax
 or_load si,si
 jz .success
 jmp short .publish
 nop
.replace:
 mov ax,[bp+4]
 mov_load bx,di
 shl bx,1
 mov [bx+si],ax
 jmp short .success
 nop
.append:
 cmp word [bp-4],byte 0
 jnz .success
 or_load di,di
 jge .size
 neg ax
 mov_load di,ax
.size:
 lea ax,[di+2]
 shl ax,1
 push ax
 push si
 call environment_realloc
 add sp,byte 4
 mov_load si,ax
 or_load si,si
 jnz .store
 jmp near .failed
.store:
 mov ax,[bp+4]
 mov_load bx,di
 shl bx,1
 mov [bx+si],ax
 add_load bx,si
 mov word [bx+2],0
.publish:
 mov [environment_table],si
.success:
 sub_load ax,ax
.done:
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_ENVIRONMENT_UNIT=0 || ASPECT_ENVIRONMENT_UNIT=6
environment_find_native:
 push bp
 mov_load bp,sp
 sub sp,byte 8
 push di
 push si
 mov ax,[environment_table]
 mov [bp-2],ax
 jmp short .next
.entry:
 mov si,[bp+4]
 mov ax,[bp+6]
 mov [bp-4],ax
 jmp short .compare_next
 nop
.compare:
 inc di
 lodsb
 cmp [di-1],al
 jnz .compared
 dec word [bp-4]
.compare_next:
 cmp word [bp-4],byte 0
 jnz .compare
.compared:
 cmp word [bp-4],byte 0
 jnz .advance
 cmp byte [di],0x3d
 jz .found
 cmp byte [di],0
 jnz .advance
.found:
 mov ax,[bp-2]
 sub ax,[environment_table]
 sar ax,1
 jmp short .done
 nop
.advance:
 add word [bp-2],byte 2
.next:
 mov bx,[bp-2]
 mov di,[bx]
 or_load di,di
 jnz .entry
 mov_load ax,bx
 sub ax,[environment_table]
 sar ax,1
 neg ax
.done:
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%ifndef ASPECT_ENVIRONMENT_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
environment_empty: db 0
environment_buffer: dw environment_storage
environment_storage: times 81 db 0
%endif
