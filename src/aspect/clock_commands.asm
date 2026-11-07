; Recovered PCPlus2.01 DATE/TIME handlers and resident time formatter.
; DS=SS, near cdecl; bounded integer RET4. Neither command changes comparison.
; DATE preserves native year-minus1900 text. TIME0 is12hour, TIME1 is24hour.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CLOCK_FLAT
%if ASPECT_CLOCK_UNIT=1
ORG 0xe689
%elif ASPECT_CLOCK_UNIT=2
ORG 0xe909
%elif ASPECT_CLOCK_UNIT=3
ORG 0x498b
%endif
%define directory_accounting_date_original 0x36d4
%define aspect_string_read_destination 0xdf0b
%define program_strcpy 0x8268
%define aspect_string_flush 0xe0a4
%define aspect_string_bounded_integer 0xdd68
%if ASPECT_CLOCK_UNIT!=3
%define aspect_clock_time_format 0x498b
%endif
%define aspect_receive_native_time 0x778c
%define clock_sprintf 0x82b6
%define clock_format24 0x4786
%define clock_pm 0x4796
%define clock_am 0x4799
%define clock_format12 0x479c
%define clock_buffer 0x8f4c
%else
%define ASPECT_CLOCK_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_clock_date,aspect_clock_time,aspect_clock_time_format
extern directory_accounting_date_original,aspect_receive_native_time
extern aspect_string_read_destination,program_strcpy,aspect_string_flush
extern aspect_string_bounded_integer,_runtime_enum_sprintf
%define clock_sprintf _runtime_enum_sprintf
global directory_accounting_date_buffer,directory_accounting_date_format
global directory_accounting_sprintf
directory_accounting_sprintf:
 jmp _runtime_enum_sprintf
%endif
%if ASPECT_CLOCK_UNIT=0 || ASPECT_CLOCK_UNIT=1
aspect_clock_date:
 call directory_accounting_date_original
 push ax
 call aspect_string_read_destination
 push ax
 call program_strcpy
 pop bx
 pop bx
 call aspect_string_flush
 ret
%endif
%if ASPECT_CLOCK_UNIT=0 || ASPECT_CLOCK_UNIT=2
aspect_clock_time:
 push si
 call aspect_string_read_destination
 mov_load si,ax
 sub_load ax,ax
 push ax
 mov ax,1
 push ax
 call aspect_string_bounded_integer
 push ax
 call aspect_clock_time_format
 pop bx
 push ax
 push si
 call program_strcpy
 pop bx
 pop bx
 call aspect_string_flush
 pop si
 ret
%endif
%if ASPECT_CLOCK_UNIT=0 || ASPECT_CLOCK_UNIT=3
aspect_clock_time_format:
 push bp
 mov_load bp,sp
 sub sp,byte 8
 push si
 sub_load si,si
 lea ax,[bp-8]
 push ax
 call aspect_receive_native_time
 cmp word [bp+4],byte 0
 jz .twelve
 push word [bp-2]
 push word [bp-4]
 push word [bp-6]
 mov ax,clock_format24
 push ax
 mov ax,clock_buffer
 push ax
 call clock_sprintf
 add sp,byte 10
 jmp short .done
.twelve:
 cmp word [bp-6],byte 11
 jle .hour
 cmp word [bp-6],byte 12
 jle .pm
 sub word [bp-6],byte 12
.pm:
 mov si,1
.hour:
 cmp word [bp-6],byte 0
 jnz .suffix
 mov word [bp-6],12
.suffix:
 or_load si,si
 jz .am
 mov ax,clock_pm
 jmp short .format
.am:
 mov ax,clock_am
.format:
 push ax
 push word [bp-2]
 push word [bp-4]
 push word [bp-6]
 mov ax,clock_format12
 push ax
 mov ax,clock_buffer
 push ax
 call clock_sprintf
 add sp,byte 12
.done:
 mov ax,clock_buffer
 pop si
 mov_load sp,bp
 pop bp
 ret
%endif
%ifndef ASPECT_CLOCK_FLAT
GROUP DGROUP _DATA
SEGMENT _DATA public class=DATA use16
directory_accounting_date_buffer: times 16 db 0
directory_accounting_date_format: db '%2.2d/%2.2d/%2.2d',0
clock_buffer: times 16 db 0
; Native CRT discards this trailing percent; the private formatter does too.
clock_format24: db '%02d:%02d:%02d%',0
clock_pm: db 'PM',0
clock_am: db 'AM',0
clock_format12: db '%02d:%02d:%02d%2s',0
%endif
