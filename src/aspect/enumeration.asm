; Native PCPlus2.01 file enumeration. Numeric provenance in unit fixture.
; Native services leave DOS DTA selected; application wrapper must save/restore
; it around every search, including FINDNEXT after unrelated DOS operations.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_ENUM_FLAT
%if ASPECT_ENUM_UNIT=1
ORG 0xefb0
%elif ASPECT_ENUM_UNIT=2
ORG 0xefe8
%elif ASPECT_ENUM_UNIT=3
ORG 0xeda4
%elif ASPECT_ENUM_UNIT=4
ORG 0xee23
%elif ASPECT_ENUM_UNIT=5
ORG 0xeffb
%elif ASPECT_ENUM_UNIT=6
ORG 0x5b54
%elif ASPECT_ENUM_UNIT=7
ORG 0xda6a
%elif ASPECT_ENUM_UNIT=8
ORG 0xdac5
%endif
%define enum_mask 0xce6a
%define enum_dta 0xceb4
%define enum_filename 0xced2
%define enum_size 0xcece
%define enum_attr 0xcec9
%define enum_line 0xce3e
%define enum_extension 0xe130
%define enum_attributes 0xe132
%define enum_found 0xe39c
%define enum_empty 0x4942
%define enum_dot 0x77bc
%define enum_dotdot 0x77be
%define enum_ctype 0x7caf
%define enum_search_function 0x5d86
%define enum_directory_format 0x5d87
%define enum_file_format 0x5daf
%define enum_string_read 0xdf04
%define enum_option_flag 0xe0e4
%define enum_warning 0x4efb
%define enum_strcpy 0x8268
%define enum_strchr 0x8c2a
%define enum_memmove 0x85b4
%define enum_strcmp 0x9476
%define enum_sprintf 0x82b6
%if ASPECT_ENUM_UNIT!=3
%define enum_parse_attributes 0xeda4
%endif
%if ASPECT_ENUM_UNIT!=4
%define enum_format_attributes 0xee23
%endif
%if ASPECT_ENUM_UNIT!=5
%define enum_fix_result 0xeffb
%endif
%if ASPECT_ENUM_UNIT!=6
%define enum_first_service 0x5b54
%define enum_next_service 0x5b68
%endif
%else
%define ASPECT_ENUM_UNIT 0
%macro CEXPORT 1
 global _%1
 _%1 equ %1
%endmacro
SEGMENT _TEXT public class=CODE use16
CEXPORT enum_first_service
CEXPORT enum_next_service
CEXPORT enum_fix_result
CEXPORT enum_mask
CEXPORT enum_line
CEXPORT enum_dta
CEXPORT enum_attributes
CEXPORT enum_extension
CEXPORT enum_filename
CEXPORT enum_attr
global aspect_enumeration_first,aspect_enumeration_next,enum_parse_attributes,enum_format_attributes,enum_fix_result
global enum_first_service,enum_next_service
extern aspect_string_read,aspect_string_option_flag,aspect_string_error,aspect_find_found
extern program_strcpy,_runtime_enum_strcmp,_runtime_enum_strchr,_runtime_enum_memmove,_runtime_enum_sprintf
%define enum_strchr _runtime_enum_strchr
%define enum_memmove _runtime_enum_memmove
%define enum_sprintf _runtime_enum_sprintf
%define enum_string_read aspect_string_read
%define enum_option_flag aspect_string_option_flag
%define enum_warning aspect_string_error
%define enum_found aspect_find_found
%define enum_strcpy program_strcpy
%define enum_strcmp _runtime_enum_strcmp
%endif
%ifdef ASPECT_ENUM_FLAT
%define enum_first_callback enum_first_service
%define enum_next_callback enum_next_service
%else
%ifdef ASPECT_ENUM_RUNTIME
extern _runtime_enum_first,_runtime_enum_next
%define enum_first_callback _runtime_enum_first
%define enum_next_callback _runtime_enum_next
%else
%define enum_first_callback enum_first_service
%define enum_next_callback enum_next_service
%endif
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=1
aspect_enumeration_first:
 push si
 call enum_string_read
 push ax
 mov ax,enum_mask
 push ax
 call enum_strcpy
 pop bx
 pop bx
 call enum_option_flag
 or_load ax,ax
 jz .default
 call enum_string_read
 push ax
 mov ax,1
 push ax
 call enum_parse_attributes
 mov_load si,ax
 jmp short .search
.default:
 mov si,1
.search:
 push si
 call enum_first_callback
 pop bx
 mov [enum_found],ax
 or_load ax,ax
 jz .done
 call enum_fix_result
.done:
 pop si
 ret
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=2
aspect_enumeration_next:
 mov ax,1
 push ax
 call enum_next_callback
 pop bx
 mov [enum_found],ax
 or_load ax,ax
 jz .done
 call enum_fix_result
.done:
 ret
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=3
enum_parse_attributes:
 push bp
 mov_load bp,sp
 push di
 push si
 sub_load si,si
 mov di,[bp+6]
.loop:
 cmp byte [di],0
 je .done
 mov bl,[di]
 sub_load bh,bh
 test byte [bx+enum_ctype],2
 jz .literal
 mov_load al,bl
 sub_load ah,ah
 sub ax,strict word 0x20
 jmp short .classified
.literal:
 mov al,[di]
 sub_load ah,ah
.classified:
 cmp ax,strict word 0x56
 je .volume
 ja .invalid
 sub al,0x41
 jz .archive
 sub al,3
 jz .directory
 sub al,4
 jz .hidden
 sub al,0xa
 jz .readonly
 dec al
 jz .system
.invalid:
 sub_load ax,ax
 push ax
 call enum_warning
.advance:
 inc di
 jmp short .loop
.archive:
 or si,byte 0x20
 jmp short .advance
.hidden:
 or si,byte 2
 jmp short .advance
.readonly:
 or si,byte 1
 jmp short .advance
.system:
 or si,byte 4
 jmp short .advance
.volume:
 cmp word [bp+4],byte 0
 jz .directory
 or si,byte 8
 jmp short .advance
.directory:
 cmp word [bp+4],byte 0
 jz .invalid
 or si,byte 0x10
 jmp short .advance
.done:
 mov_load ax,si
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret 4
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=4
enum_format_attributes:
 push bp
 mov_load bp,sp
 mov dx,[bp+6]
 mov bx,[bp+4]
 test dl,1
 jz .hidden
 inc bx
 mov byte [bx-1],'R'
.hidden:
 test dl,2
 jz .system
 inc bx
 mov byte [bx-1],'H'
.system:
 test dl,4
 jz .archive
 inc bx
 mov byte [bx-1],'S'
.archive:
 test dl,0x20
 jz .directory
 inc bx
 mov byte [bx-1],'A'
.directory:
 test dl,0x10
 jz .volume
 inc bx
 mov byte [bx-1],'D'
.volume:
 test dl,8
 jz .done
 inc bx
 mov byte [bx-1],'V'
.done:
 mov byte [bx],0
 pop bp
 ret 4
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=5
enum_fix_result:
 push si
 mov si,enum_line+11
 jmp short .trim
.space:
 dec si
.trim:
 cmp byte [si],0x20
 jz .space
 mov byte [si+1],0
 mov word [enum_extension],enum_empty
 mov ax,0x2e
 push ax
 mov ax,enum_line
 push ax
 call enum_strchr
 pop bx
 pop bx
 mov_load si,ax
 test byte [enum_attr],8
 jz .ordinary
%ifdef ASPECT_ENUM_RUNTIME
 ; Native volume fixup otherwise passes a null strchr result to memmove.
 or_load si,si
 jz .attributes
%endif
 mov ax,0xc
 push ax
 lea ax,[si+1]
 push ax
 push si
 call enum_memmove
 add sp,byte 6
 mov ax,enum_line
 push ax
 mov ax,enum_filename
 push ax
 call enum_strcpy
 pop bx
 pop bx
 jmp short .attributes
.ordinary:
 or_load si,si
 jz .attributes
 test byte [enum_attr],0x10
 jz .split
 mov ax,enum_dot
 push ax
 mov ax,enum_filename
 push ax
 call enum_strcmp
 pop bx
 pop bx
 or_load ax,ax
 jz .attributes
 mov ax,enum_dotdot
 push ax
 mov ax,enum_filename
 push ax
 call enum_strcmp
 pop bx
 pop bx
 or_load ax,ax
 jz .attributes
.split:
 mov byte [si],0
 lea ax,[si+1]
 mov [enum_extension],ax
.attributes:
 mov byte [enum_line+30],0
 mov al,[enum_attr]
 cbw
 push ax
 mov ax,enum_attributes
 push ax
 call enum_format_attributes
 pop si
 ret
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=6
enum_first_service:
 push di
 mov ah,0x1a
 mov dx,enum_dta
 mov_load di,dx
 int 0x21
 pop di
 mov byte [enum_search_function],0x4e
 call enum_search
 ret
enum_next_service:
 mov byte [enum_search_function],0x4f
 call enum_search
 ret
enum_search:
 push bp
 mov_load bp,sp
 push di
 mov di,enum_dta
 mov ah,[enum_search_function]
 cmp ah,0x4f
 je .kernel
 mov cx,[bp+6]
 mov dx,enum_mask
.kernel:
 int 0x21
 jnc .found
 jmp short .not_found
.found:
 cmp word [bp+6],byte 0
 jz .unformatted
 cmp byte [di+0x15],0x10
 jnz .file
 mov dx,.directory_output
 jmp short .date
.directory_output:
 mov ax,enum_filename
 push ax
 mov ax,enum_directory_format
 push ax
 mov ax,enum_line
 push ax
 call enum_sprintf
 add sp,byte 0x10
 jmp short .success
.unformatted:
 mov ax,enum_filename
 push ax
 mov ax,enum_line
 push ax
 call enum_strcpy
 add sp,byte 4
 jmp short .success
.file:
 mov dx,.file_output
 jmp short .date
.file_output:
 push word [enum_size+2]
 push word [enum_size]
 mov ax,enum_filename
 push ax
 mov ax,enum_file_format
 push ax
 mov ax,enum_line
 push ax
 call enum_sprintf
 add sp,byte 0x14
.success:
 mov ax,1
 pop di
 pop bp
 ret
.not_found:
 xor_load ax,ax
 jmp short .success+3
.date:
 mov ax,[di+0x16]
 mov_load bx,ax
 mov cl,5
 shr ax,cl
 and ax,strict word 0x3f
 push ax
 mov cl,0xb
 shr bx,cl
 and bx,byte 0x1f
 push bx
 mov ax,[di+0x18]
 mov_load bx,ax
 mov cl,9
 shr ax,cl
 and ax,strict word 0x7f
 add ax,strict word 0x50
 push ax
 mov_load ax,bx
 and ax,strict word 0x1f
 push ax
 mov cl,5
 shr bx,cl
 and bx,byte 0xf
 push bx
 jmp dx
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=7
global aspect_enumeration_size
aspect_enumeration_size:
 mov ax,[enum_size]
 mov dx,[enum_size+2]
 ret
%endif
%if ASPECT_ENUM_UNIT=0 || ASPECT_ENUM_UNIT=8
global aspect_enumeration_attributes,aspect_enumeration_date,aspect_enumeration_extension
 global aspect_enumeration_filename,aspect_enumeration_basename,aspect_enumeration_time
aspect_enumeration_attributes:
 mov ax,enum_attributes
 ret
aspect_enumeration_date:
 cmp byte [enum_line+22],0x20
 jnz .date
 mov ax,1
 jmp short .done
.date:
 sub_load ax,ax
.done:
 add ax,strict word enum_line+22
 ret
aspect_enumeration_extension:
 mov ax,[enum_extension]
 ret
aspect_enumeration_filename:
 mov ax,enum_filename
 ret
aspect_enumeration_basename:
 mov ax,enum_line
 ret
aspect_enumeration_time:
 mov ax,enum_line+32
 ret
%endif
%ifndef ASPECT_ENUM_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
global enum_mask,enum_dta,enum_filename,enum_size,enum_attr,enum_line,enum_extension,enum_attributes
enum_line: times 44 db 0
enum_mask: times 81 db 0
enum_dta: times 21 db 0
enum_attr: db 0
 dw 0,0
enum_size: dd 0
enum_filename: times 13 db 0
enum_extension: dw enum_empty
enum_attributes: times 7 db 0
enum_empty: db 0
enum_dot: db '.',0
enum_dotdot: db '..',0
enum_search_function: db 0
enum_directory_format: db '%-12s   <DIR>  %2u-%.2u-%.2u  %.2u:%.2u',0
enum_file_format: db '%-12s  %6lu  %2u-%.2u-%.2u  %.2u:%.2u',0
enum_ctype:
%assign c 0
%rep 256
%if c>='a' && c<='z'
 db 2
%else
 db 0
%endif
%assign c c+1
%endrep
%endif
