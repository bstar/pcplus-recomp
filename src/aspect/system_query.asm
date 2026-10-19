; Native PCPlus2.01 DISKFREE, DOSVER, GETDIR and DOS interrupt helpers.
; Flat source-only range/hash fixture owns native identity. DOSVER's maintained
; destination/flush adaptation is explicit under ASPECT_SYSTEM_QUERY_RUNTIME.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SYSTEM_QUERY_FLAT
%if ASPECT_SYSTEM_QUERY_UNIT=1
ORG 0xe6b9
%elif ASPECT_SYSTEM_QUERY_UNIT=2
ORG 0xe6d1
%elif ASPECT_SYSTEM_QUERY_UNIT=3
ORG 0xe721
%elif ASPECT_SYSTEM_QUERY_UNIT=4
ORG 0x5cce
%elif ASPECT_SYSTEM_QUERY_UNIT=5
ORG 0x5cd5
%elif ASPECT_SYSTEM_QUERY_UNIT=6
ORG 0x78ba
%elif ASPECT_SYSTEM_QUERY_UNIT=7
ORG 0xf2a4
%endif
%define aspect_operand_read_integer 0xdc48
%define aspect_expr_long_address 0xde92
%define aspect_string_read 0xdf04
%define aspect_string_read_destination 0xdf0b
%define aspect_string_flush 0xe0a4
%define aspect_string_compare_result 0xd124
%define system_sprintf 0x82b6
%define system_version_format 0x778e
%define system_directory_format 0x7796
%if ASPECT_SYSTEM_QUERY_UNIT!=4
%define system_current_drive 0x5cce
%endif
%if ASPECT_SYSTEM_QUERY_UNIT!=5
%define system_current_directory 0x5cd5
%endif
%if ASPECT_SYSTEM_QUERY_UNIT!=6
%define system_disk_free 0x78ba
%endif
%if ASPECT_SYSTEM_QUERY_UNIT!=7
%define system_dos_version 0xf2a4
%endif
%else
%define ASPECT_SYSTEM_QUERY_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_system_diskfree,aspect_system_dosver,aspect_system_getdir
extern aspect_operand_read_integer,aspect_expr_long_address
extern aspect_string_read,aspect_string_read_destination,aspect_string_flush
extern aspect_string_compare_result,_runtime_enum_sprintf
%define system_sprintf _runtime_enum_sprintf
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=1
aspect_system_diskfree:
 push di
 push si
 call aspect_operand_read_integer
 mov_load di,ax
 call aspect_expr_long_address
 mov_load si,ax
 push di
 call system_disk_free
 mov [si],ax
 mov [si+2],dx
 pop si
 pop di
 ret
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=2
aspect_system_dosver:
 push si
 call system_dos_version
 mov_load si,ax
 mov_load al,ah
 sub_load ah,ah
 push ax
 mov_load ax,si
 sub_load ah,ah
 push ax
 mov ax,system_version_format
 push ax
%ifdef ASPECT_SYSTEM_QUERY_RUNTIME
 call aspect_string_read_destination
%else
 call aspect_string_read
%endif
 push ax
 call system_sprintf
 add sp,byte 8
%ifdef ASPECT_SYSTEM_QUERY_RUNTIME
 call aspect_string_flush
%endif
 pop si
 ret
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=3
aspect_system_getdir:
 push di
 push si
 call aspect_operand_read_integer
 mov_load si,ax
 or_load si,si
 jnz .drive
 call system_current_drive
 mov_load si,ax
 inc si
.drive:
 lea ax,[si+0x40]
 push ax
 mov ax,system_directory_format
 push ax
 call aspect_string_read_destination
 push ax
 mov_load di,ax
 call system_sprintf
 add sp,byte 6
 lea ax,[di+3]
 push ax
 push si
 call system_current_directory
 pop bx
 pop bx
 mov [aspect_string_compare_result],ax
 call aspect_string_flush
 pop si
 pop di
 ret
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=4
system_current_drive:
 mov ah,0x19
 int 0x21
 xor_load ah,ah
 ret
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=5
system_current_directory:
 mov_load bx,sp
 push si
 mov ah,0x47
 mov dx,[bx+2]
 mov si,[bx+4]
 int 0x21
 jc .done
 xor_load ax,ax
.done:
 pop si
 ret
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=6
system_disk_free:
 mov_load bx,sp
 mov dx,[bx+2]
 mov ah,0x36
 int 0x21
 cmp ax,strict word 0xffff
 jz .failed
 mul cx
 mul bx
.done:
 ret 2
.failed:
 cwd
 jmp short .done
%endif
%if ASPECT_SYSTEM_QUERY_UNIT=0 || ASPECT_SYSTEM_QUERY_UNIT=7
system_dos_version:
 mov ah,0x30
 int 0x21
 ret
%endif
%ifndef ASPECT_SYSTEM_QUERY_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
system_version_format: db '%d.%02d',0
system_directory_format: db '%c:',92,0
%endif
