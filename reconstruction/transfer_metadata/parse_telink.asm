; Exact original transfer metadata instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_METADATA_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global metadata_parse_telink
global metadata_at_e4c3
global metadata_at_e4c6
global metadata_at_e4c9
global metadata_at_e4cd
global metadata_at_e4cf
global metadata_at_e4d1
global metadata_at_e4d3
global metadata_at_e4d5
global metadata_at_e4d9
global metadata_at_e4db
global metadata_at_e4dd
global metadata_at_e4df
global metadata_at_e4e1
global metadata_at_e4e3
global metadata_at_e4e7
global metadata_at_e4eb
global metadata_at_e4ec
global metadata_at_e4ee
global metadata_at_e4f2
global metadata_at_e4f5
global metadata_at_e4f8
global metadata_at_e4fa
global metadata_at_e4fc
global metadata_at_e4ff
global metadata_at_e502
global metadata_at_e504
global metadata_at_e507
global metadata_at_e509
global metadata_at_e50c
global metadata_at_e50f
global metadata_at_e510
global metadata_at_e513
global metadata_at_e514
global metadata_at_e517
global metadata_at_e518
global metadata_at_e51b
global metadata_at_e51e
global metadata_at_e520
global metadata_at_e521
global metadata_at_e524
global metadata_at_e527
global metadata_at_e528
extern metadata_buffer_pointer
extern metadata_size_low
extern metadata_size_high
extern metadata_strncpy
extern metadata_filename
extern metadata_time
extern metadata_date
extern metadata_display_start
%else
ORG 0xe4c2
%define metadata_buffer_pointer 0x39c0
%define metadata_size_low 0x9006
%define metadata_size_high 0x9008
%define metadata_strncpy 0x9888
%define metadata_filename 0xcb68
%define metadata_time 0xcd3a
%define metadata_date 0xcd76
%define metadata_display_start 0xee10
%endif
%include "encodings.inc"
metadata_parse_telink: push si
metadata_at_e4c3: mov si,0x3
metadata_at_e4c6: mov ax,[metadata_size_low]
metadata_at_e4c9: mov dx,[metadata_size_high]
metadata_at_e4cd: mov_load dh,dl
metadata_at_e4cf: mov_load dl,ah
metadata_at_e4d1: mov_load ah,al
metadata_at_e4d3: sub_load al,al
metadata_at_e4d5: mov bx,[metadata_buffer_pointer]
metadata_at_e4d9: mov cl,[bx+si]
metadata_at_e4db: sub_load ch,ch
metadata_at_e4dd: sub_load bx,bx
metadata_at_e4df: add_load cx,ax
metadata_at_e4e1: adc_load bx,dx
metadata_at_e4e3: mov [metadata_size_low],cx
metadata_at_e4e7: mov [metadata_size_high],bx
metadata_at_e4eb: dec si
metadata_at_e4ec: jns short metadata_at_e4c6
metadata_at_e4ee: mov bx,[metadata_buffer_pointer]
metadata_at_e4f2: mov ah,[bx+0x5]
metadata_at_e4f5: mov cl,[bx+0x4]
metadata_at_e4f8: sub_load ch,ch
metadata_at_e4fa: or_load ax,cx
metadata_at_e4fc: mov [metadata_date],ax
metadata_at_e4ff: mov ah,[bx+0x7]
metadata_at_e502: sub_load al,al
metadata_at_e504: mov cl,[bx+0x6]
metadata_at_e507: or_load ax,cx
metadata_at_e509: mov [metadata_time],ax
metadata_at_e50c: mov ax,0x10
metadata_at_e50f: push ax
metadata_at_e510: lea ax,[bx+0x8]
metadata_at_e513: push ax
metadata_at_e514: mov ax,metadata_filename
metadata_at_e517: push ax
metadata_at_e518: call metadata_strncpy
metadata_at_e51b: add sp,0x6
metadata_at_e51e: sub_load ax,ax
metadata_at_e520: push ax
metadata_at_e521: call metadata_display_start
metadata_at_e524: add sp,0x2
metadata_at_e527: pop si
metadata_at_e528: ret
