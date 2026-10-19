; Exact PCPlus2.01 file date/time wrappers, shared core, parsers and DOS57
; helpers. Flat facts in fixture. Runtime selects writable GET destinations,
; flushes them, and copies SET inputs before the destructive native parsers.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_FILE_TIMES_FLAT
%if ASPECT_FILE_TIMES_UNIT=1
ORG 0xed85
%elif ASPECT_FILE_TIMES_UNIT=2
ORG 0xee6f
%elif ASPECT_FILE_TIMES_UNIT=3
ORG 0xef37
%elif ASPECT_FILE_TIMES_UNIT=4
ORG 0xef84
%elif ASPECT_FILE_TIMES_UNIT=5
ORG 0xf2eb
%elif ASPECT_FILE_TIMES_UNIT=6
ORG 0xf2fc
%endif
%define aspect_string_read 0xdf04
%define aspect_string_compare_result 0xd124
%define file_times_open 0x841a
%define file_times_close 0x8318
%define file_times_sprintf 0x82b6
%define file_times_atoi 0x984e
%define file_times_mode 0x77a1
%define file_times_date_format 0x77a4
%define file_times_time_format 0x77b2
%if ASPECT_FILE_TIMES_UNIT!=2
%define file_times_core 0xee6f
%endif
%if ASPECT_FILE_TIMES_UNIT!=3
%define file_times_parse_date 0xef37
%endif
%if ASPECT_FILE_TIMES_UNIT!=4
%define file_times_parse_time 0xef84
%endif
%if ASPECT_FILE_TIMES_UNIT!=5
%define file_times_read 0xf2eb
%endif
%if ASPECT_FILE_TIMES_UNIT!=6
%define file_times_write 0xf2fc
%endif
%else
%define ASPECT_FILE_TIMES_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_file_times_get_date,aspect_file_times_get_time,aspect_file_times_set_date,aspect_file_times_set_time
extern aspect_string_read,aspect_string_read_destination,aspect_string_flush,aspect_string_compare_result
extern _runtime_file_times_open,_runtime_file_times_close,_runtime_file_times_copy
extern _runtime_enum_sprintf,aspect_conversion_atoi
%define file_times_open _runtime_file_times_open
%define file_times_close _runtime_file_times_close
%define file_times_sprintf _runtime_enum_sprintf
%define file_times_atoi aspect_conversion_atoi
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=1
aspect_file_times_get_date:
 sub_load ax,ax
 push ax
 call file_times_core
 ret
aspect_file_times_get_time:
 mov ax,1
 push ax
 call file_times_core
 ret
aspect_file_times_set_date:
 mov ax,2
 push ax
 call file_times_core
 ret
aspect_file_times_set_time:
 mov ax,3
 push ax
 call file_times_core
 ret
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=2
file_times_core:
 push bp
 mov_load bp,sp
 sub sp,byte 6
 push di
 push si
 mov ax,file_times_mode
 push ax
 call aspect_string_read
 push ax
 call file_times_open
 pop bx
 pop bx
 mov_load di,ax
 cmp di,byte 1
 sbb_load ax,ax
 neg ax
 mov [aspect_string_compare_result],ax
%ifdef ASPECT_FILE_TIMES_RUNTIME
 cmp word [bp+4],byte 2
 jae .input
 call aspect_string_read_destination
 jmp short .selected
.input:
 call aspect_string_read
 push ax
 call _runtime_file_times_copy
 pop bx
.selected:
%else
 call aspect_string_read
%endif
 mov_load si,ax
 cmp word [aspect_string_compare_result],byte 0
 jz .opened
 jmp near .done
.opened:
 mov al,[di+7]
 sub_load ah,ah
 mov [bp-6],ax
 push ax
 call file_times_read
 pop bx
 mov [bp-4],ax
 mov ax,[bp+4]
 or_load ax,ax
 jz .get_date
 dec ax
 jz .get_time
 dec ax
 jz .set_date
 dec ax
 jz .set_time
 jmp short .close
.get_date:
 mov_load ax,dx
 mov cl,9
 shr ax,cl
 add ax,strict word 0x50
 mov cx,0x64
 mov_load bx,dx
 sub_load dx,dx
 div cx
 push dx
 mov_load ax,bx
 and bx,byte 0x1f
 push bx
 and ax,strict word 0x1e0
 mov cl,5
 shr ax,cl
 push ax
 mov ax,file_times_date_format
 push ax
 push si
 call file_times_sprintf
 add sp,byte 0xa
 jmp short .close
.get_time:
 mov cl,5
 mov ax,[bp-4]
 and ax,strict word 0x7e0
 shr ax,cl
 push ax
 mov cl,0xb
 mov ax,[bp-4]
 shr ax,cl
 push ax
 mov ax,file_times_time_format
 push ax
 push si
 call file_times_sprintf
 add sp,byte 8
 jmp short .close
.set_date:
 push si
 call file_times_parse_date
 pop bx
 push ax
 push word [bp-4]
 jmp short .set
.set_time:
 push dx
 push si
 call file_times_parse_time
 pop bx
 push ax
.set:
 push word [bp-6]
 call file_times_write
 add sp,byte 6
.close:
 push di
 call file_times_close
 pop bx
.done:
%ifdef ASPECT_FILE_TIMES_RUNTIME
 cmp word [bp+4],byte 2
 jae .leave
 call aspect_string_flush
.leave:
%endif
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret 2
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=3
file_times_parse_date:
 push bp
 mov_load bp,sp
 push di
 push si
 sub_load al,al
 mov bx,[bp+4]
 mov [bx+5],al
 mov [bx+2],al
 lea ax,[bx+6]
 push ax
 call file_times_atoi
 pop bx
 mov_load si,ax
 cmp si,byte 0x50
 jnc .old_century
 add si,byte 0x14
 jmp short .month
.old_century:
 sub si,byte 0x50
.month:
 push word [bp+4]
 call file_times_atoi
 pop bx
 mov cl,5
 shl ax,cl
 mov cx,[bp+4]
 add cx,byte 3
 push cx
 mov_load di,ax
 call file_times_atoi
 pop bx
 or_load ax,di
 mov cl,9
 shl si,cl
 or_load ax,si
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=4
file_times_parse_time:
 push bp
 mov_load bp,sp
 push si
 mov bx,[bp+4]
 mov byte [bx+2],0
 push bx
 call file_times_atoi
 pop bx
 mov cx,[bp+4]
 add cx,byte 3
 push cx
 mov_load si,ax
 call file_times_atoi
 pop bx
 mov cl,5
 shl ax,cl
 mov cl,0xb
 shl si,cl
 or_load ax,si
 pop si
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=5
file_times_read:
 push bp
 mov_load bp,sp
 mov ax,0x5700
 mov bx,[bp+4]
 int 0x21
 mov_load ax,cx
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_FILE_TIMES_UNIT=0 || ASPECT_FILE_TIMES_UNIT=6
file_times_write:
 push bp
 mov_load bp,sp
 mov ax,0x5701
 mov bx,[bp+4]
 mov cx,[bp+6]
 mov dx,[bp+8]
 int 0x21
 mov_load sp,bp
 pop bp
 ret
%endif
%ifndef ASPECT_FILE_TIMES_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
file_times_mode: db 'rb',0
file_times_date_format: db '%2u-%.2u-%.2u',0
file_times_time_format: db '%.2u:%.2u',0
%endif
