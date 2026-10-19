; Native PCPlus2.01 ISFILE, GETFSIZE, RENAME and their small helpers.
; Flat addresses and instruction hashes live in the source-only unit fixture.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FILE_INFO_FLAT
%if ASPECT_FILE_INFO_UNIT=1
ORG 0xe791
%elif ASPECT_FILE_INFO_UNIT=2
ORG 0xecfa
%elif ASPECT_FILE_INFO_UNIT=3
ORG 0xe8ce
%elif ASPECT_FILE_INFO_UNIT=4
ORG 0x3673
%elif ASPECT_FILE_INFO_UNIT=5
ORG 0xf2d4
%endif
%define aspect_string_read 0xdf04
%define aspect_expr_long_address 0xde92
%define aspect_operand_read_long 0xdcc1
%define aspect_string_compare_result 0xd124
%define file_info_open 0x841a
%define file_info_close 0x8318
%define file_info_seek 0x853a
%define file_info_tell 0x8ed8
%define file_info_test_mode 0x4726
%define file_info_size_mode 0x779e
%define file_info_segment 0x77c8
%if ASPECT_FILE_INFO_UNIT!=4
%define aspect_file_info_test 0x3673
%endif
%if ASPECT_FILE_INFO_UNIT!=5
%define aspect_file_info_move 0xf2d4
%endif
%else
%define ASPECT_FILE_INFO_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_file_info_isfile,aspect_file_info_size,aspect_file_info_rename
extern aspect_string_read,aspect_expr_long_address,aspect_operand_read_long,aspect_string_compare_result
extern _runtime_file_info_open,_runtime_file_info_close,_runtime_file_info_seek,_runtime_file_info_tell
extern _runtime_file_info_segment
%define file_info_open _runtime_file_info_open
%define file_info_close _runtime_file_info_close
%define file_info_seek _runtime_file_info_seek
%define file_info_tell _runtime_file_info_tell
%define file_info_segment _runtime_file_info_segment
%endif
%if ASPECT_FILE_INFO_UNIT=0 || ASPECT_FILE_INFO_UNIT=1
aspect_file_info_isfile:
 call aspect_string_read
 push ax
 call aspect_file_info_test
 pop bx
 cmp ax,strict word 1
 sbb_load ax,ax
 neg ax
 mov [aspect_string_compare_result],ax
 ret
%endif
%if ASPECT_FILE_INFO_UNIT=0 || ASPECT_FILE_INFO_UNIT=2
aspect_file_info_size:
 push di
 push si
 mov word [aspect_string_compare_result],0
 mov ax,file_info_size_mode
 push ax
 call aspect_string_read
 push ax
 call file_info_open
 pop bx
 pop bx
 mov_load si,ax
 or_load si,si
 jz .failed
 mov ax,2
 push ax
 sub_load ax,ax
 push ax
 push ax
 push si
 call file_info_seek
 add sp,byte 8
 call aspect_expr_long_address
 mov_load di,ax
 push si
 call file_info_tell
 pop bx
 mov [di],ax
 mov [di+2],dx
 push si
 call file_info_close
 pop bx
 pop si
 pop di
 ret
.failed:
 call aspect_operand_read_long
 inc word [aspect_string_compare_result]
 pop si
 pop di
 ret
%endif
%if ASPECT_FILE_INFO_UNIT=0 || ASPECT_FILE_INFO_UNIT=3
aspect_file_info_rename:
 push si
 call aspect_string_read
 mov_load si,ax
 call aspect_string_read
 push ax
 push si
 call aspect_file_info_move
 pop bx
 pop bx
 mov [aspect_string_compare_result],ax
 pop si
 ret
%endif
%if ASPECT_FILE_INFO_UNIT=0 || ASPECT_FILE_INFO_UNIT=4
aspect_file_info_test:
 push bp
 mov_load bp,sp
 push si
 mov ax,file_info_test_mode
 push ax
 push word [bp+4]
 call file_info_open
 pop bx
 pop bx
 mov_load si,ax
 or_load si,si
 jz .failed
 push si
 call file_info_close
 pop bx
 mov ax,1
 jmp short .done
.failed:
 sub_load ax,ax
.done:
 pop si
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FILE_INFO_UNIT=0 || ASPECT_FILE_INFO_UNIT=5
aspect_file_info_move:
 mov_load bx,sp
 push di
 mov ah,0x56
 mov dx,[bx+2]
 mov es,[file_info_segment]
 mov di,[bx+4]
 int 0x21
 jc .done
 xor_load ax,ax
.done:
 pop di
 ret
%endif
%ifndef ASPECT_FILE_INFO_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
file_info_test_mode: db 'rb',0
file_info_size_mode: db 'rb',0
%endif
