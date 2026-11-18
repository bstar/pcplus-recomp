; Exact native BOX/CLEAR/LOCATE/SCROLL/GETVATTR/PUTVATTR and coordinate readers.
; Original6401ccfd; per-entry ranges/evidence in aspect_screen_commands provenance.
; Near DS=SS, DF=0. BP/SI/DI preserved by native dependencies; AX/BX/CX/DX/ES
; and FLAGS volatile. No pointer/rectangle safety is added to the native body.
; Platform imports preserve original register/stack contracts; they are not ANSI.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SCREEN_FLAT
%if ASPECT_SCREEN_UNIT=1
ORG 0xe6d1
%elif ASPECT_SCREEN_UNIT=2
ORG 0xe700
%elif ASPECT_SCREEN_UNIT=3
ORG 0xe7e5
%elif ASPECT_SCREEN_UNIT=4
ORG 0xe847
%elif ASPECT_SCREEN_UNIT=5
ORG 0xea23
%elif ASPECT_SCREEN_UNIT=6
ORG 0xea3c
%elif ASPECT_SCREEN_UNIT=7
ORG 0xeadc
%elif ASPECT_SCREEN_UNIT=8
ORG 0xddcd
%elif ASPECT_SCREEN_UNIT=9
ORG 0xddd8
%elif ASPECT_SCREEN_UNIT=10
ORG 0xde27
%else
%error Select ASPECT_SCREEN_UNIT1..10
%endif
%define screen_position 0xde27
%define screen_row 0xddcd
%define screen_column 0xddd8
%define screen_physical_offset 0xeadc
%define aspect_string_bounded_integer 0xdd68
%define aspect_string_byte_operand 0xdde3
%define aspect_string_option_flag 0xe0e4
%define aspect_string_store_integer 0xde3a
%define aspect_screen_scroll_rectangle 0x6edc
%define aspect_screen_draw_box 0x4056
%define aspect_screen_reset_attribute 0x24da
%define aspect_screen_clear_home 0x24e2
%define aspect_screen_set_cursor 0x1bbe
%define aspect_screen_read_video_byte 0x6fa0
%define aspect_screen_write_video_byte 0x6c84
%define aspect_screen_normal 0x1d32
%define aspect_screen_configured_wide 0x1d2e
%define aspect_screen_physical_rows 0x7a74
%define aspect_screen_physical_last_row 0x7a80
%define aspect_screen_physical_last_column 0x7a7e
%define aspect_screen_physical_stride 0x7a7a
%else
%define ASPECT_SCREEN_UNIT 0
%ifdef ASPECT_SCREEN_FAR
SEGMENT SCRIPT_SCREEN_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global aspect_screen_box,aspect_screen_clear,aspect_screen_locate,aspect_screen_scroll
global aspect_screen_getvattr,aspect_screen_putvattr,aspect_screen_physical_offset
global aspect_screen_row,aspect_screen_column,aspect_screen_position
extern aspect_string_bounded_integer,aspect_string_byte_operand
extern aspect_string_option_flag,aspect_string_store_integer
extern aspect_screen_scroll_rectangle,aspect_screen_draw_box
extern aspect_screen_reset_attribute,aspect_screen_clear_home,aspect_screen_set_cursor
extern aspect_screen_read_video_byte,aspect_screen_write_video_byte
extern aspect_screen_normal,aspect_screen_configured_wide,aspect_screen_physical_rows
extern aspect_screen_physical_last_row,aspect_screen_physical_last_column
extern aspect_screen_physical_stride
%define screen_position aspect_screen_position
%define screen_row aspect_screen_row
%define screen_column aspect_screen_column
%define screen_physical_offset aspect_screen_physical_offset
%endif

%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=1
aspect_screen_box:
 push bp
 mov_load bp,sp
 sub sp,2
 push di
 push si
 call screen_position
 mov_load di,ax
 call screen_position
 mov_load si,ax
 sub_load ax,ax
 push ax
 push di
 push si
 call aspect_string_byte_operand
 push ax
 mov [bp-2],ax
 call aspect_screen_scroll_rectangle
 push di
 push si
 push word [bp-2]
 call aspect_screen_draw_box
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=2
aspect_screen_clear:
 call aspect_string_option_flag
 or_load ax,ax
 jz .clear_home
 call aspect_string_byte_operand
 mov [aspect_screen_normal],ax
 call aspect_screen_reset_attribute
.clear_home:
 jmp aspect_screen_clear_home
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=3
aspect_screen_locate:
 push si
 call screen_row
 mov_load si,ax
 cmp word [aspect_screen_configured_wide],0
 jnz .wide
 call screen_column
 jmp short .cursor
.wide:
 sub_load ax,ax
 push ax
 mov ax,0x83
 push ax
 call aspect_string_bounded_integer
.cursor:
 mov_load dx,ax
 mov_load ax,si
 call aspect_screen_set_cursor
 pop si
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=4
aspect_screen_scroll:
 sub_load ax,ax
 push ax
 push word [aspect_screen_physical_rows]
 call aspect_string_bounded_integer
 push ax
 call screen_position
 push ax
 call screen_position
 push ax
 call aspect_string_byte_operand
 push ax
 call aspect_screen_scroll_rectangle
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=5
aspect_screen_getvattr:
 call screen_physical_offset
 inc ax
 push ax
 call aspect_screen_read_video_byte
 push ax
 call aspect_string_store_integer
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=6
aspect_screen_putvattr:
 push si
 call screen_physical_offset
 mov_load si,ax
 inc si
 call aspect_string_byte_operand
 push ax
 push si
 call aspect_screen_write_video_byte
 pop si
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=7
aspect_screen_physical_offset:
 push si
 call screen_row
 imul word [aspect_screen_physical_stride]
 mov_load si,ax
 call screen_column
 shl ax,1
 add_load ax,si
 pop si
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=8
aspect_screen_row:
 sub_load ax,ax
 push ax
 push word [aspect_screen_physical_last_row]
 call aspect_string_bounded_integer
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=9
aspect_screen_column:
 sub_load ax,ax
 push ax
 push word [aspect_screen_physical_last_column]
 call aspect_string_bounded_integer
 ret
%endif
%if ASPECT_SCREEN_UNIT=0 || ASPECT_SCREEN_UNIT=10
aspect_screen_position:
 push si
 call screen_row
 mov_load si,ax
 call screen_column
 mov_load cx,si
 mov_load ch,cl
 sub_load cl,cl
 or_load ax,cx
 pop si
 ret
%endif
