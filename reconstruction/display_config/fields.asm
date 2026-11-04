; Original overlay19 EDD1..EE22 ASPECT SET/FETCH field handlers,82 exact bytes.
; Operand reader, integer destination and error services remain explicit external boundaries.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_CONFIG_OMF
SEGMENT _TEXT public class=CODE use16
global display_config_video,display_config_rows
extern config_query_mode,preferred_video_mode,preferred_display_rows,config_error
extern config_read_video_mode,config_read_integer,config_store_integer,config_report_error
%else
ORG 0xedd1
%define config_query_mode 0xe38e
%define preferred_video_mode 0x2070
%define preferred_display_rows 0x1d4e
%define config_error 0xe378
%define config_read_video_mode 0xddee
%define config_read_integer 0xdc48
%define config_store_integer 0xde3a
%define config_report_error 0x4efb
%endif
display_config_video:
 cmp word [config_query_mode],byte 0
 jne short .output
 call config_read_video_mode
 mov [preferred_video_mode],ax
 ret
.output:
 push word [preferred_video_mode]
 call config_store_integer
 ret
display_config_rows:
 push si
 cmp word [config_query_mode],byte 0
 jne short .output
 call config_read_integer
 mov_load si,ax
 cmp si,byte 28
 je short .store
 cmp si,byte 43
 je short .store
 cmp si,byte 50
 je short .store
 mov ax,1
 push ax
 call config_report_error
 cmp word [config_error],byte 0
 je short .store
 mov si,43
.store:
 mov [preferred_display_rows],si
 pop si
 ret
.output:
 push word [preferred_display_rows]
 call config_store_integer
 pop si
 ret
