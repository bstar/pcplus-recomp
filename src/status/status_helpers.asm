; Exact native status helpers; docs/STATUS_HELPERS.md. DS=SS.
; OMF imports may be renamed with NASM -Dsymbol=replacement.
; -DSTATUS_HELPERS_CONFIG selects CONFIG_CODE classFARCODE.
; Segment/class can also be set explicitly; near callees must share it.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef STATUS_HELPERS_FLAT
%if STATUS_HELPERS_UNIT=1
ORG 0x75e8
%endif
%if STATUS_HELPERS_UNIT=2
ORG 0x7630
%endif
%if STATUS_HELPERS_UNIT=3
ORG 0x3226
%endif
%if STATUS_HELPERS_UNIT=4
ORG 0x7e0e
%endif
%define status_sprintf 0x82b6
%define ui_write_string 0x6bf0
%if STATUS_HELPERS_UNIT!=4
%define status_cga_byte 0x7e0e
%endif
%define terminal_reset_status_fill 0x4097
%define program_strlen 0x8d18
%define ui_flow_region_cells 0x3250
%define ui_flow_coordinate_base 0x7a84
%define reset_data_1f6c 0x1f6c
%define text_video_segment 0x7a78
%define text_cga_status_port 0x7a8e
%else
%define STATUS_HELPERS_UNIT 0
%ifdef STATUS_HELPERS_CONFIG
%ifndef STATUS_HELPERS_SEGMENT
%define STATUS_HELPERS_SEGMENT CONFIG_CODE
%endif
%ifndef STATUS_HELPERS_CLASS
%define STATUS_HELPERS_CLASS FARCODE
%endif
%endif
%ifndef STATUS_HELPERS_SEGMENT
%define STATUS_HELPERS_SEGMENT _TEXT
%endif
%ifndef STATUS_HELPERS_CLASS
%define STATUS_HELPERS_CLASS CODE
%endif
SEGMENT STATUS_HELPERS_SEGMENT public class=STATUS_HELPERS_CLASS use16
global status_ui_printf
global status_character_fill
global status_message
global status_cga_byte
extern status_sprintf
extern ui_write_string
extern terminal_reset_status_fill
extern program_strlen
extern ui_flow_region_cells
extern ui_flow_coordinate_base
extern reset_data_1f6c
extern text_video_segment
extern text_cga_status_port
%endif
%if STATUS_HELPERS_UNIT=0 || STATUS_HELPERS_UNIT=1
status_ui_printf:
status_loc_75e8:
 push bp
status_loc_75e9:
 mov_load bp, sp
status_loc_75eb:
 sub sp, 0x88
status_loc_75ef:
 push word [bp + 0x1e]
status_loc_75f2:
 push word [bp + 0x1c]
status_loc_75f5:
 push word [bp + 0x1a]
status_loc_75f8:
 push word [bp + 0x18]
status_loc_75fb:
 push word [bp + 0x16]
status_loc_75fe:
 push word [bp + 0x14]
status_loc_7601:
 push word [bp + 0x12]
status_loc_7604:
 push word [bp + 0x10]
status_loc_7607:
 push word [bp + 0xe]
status_loc_760a:
 push word [bp + 0xc]
status_loc_760d:
 push word [bp + 0xa]
status_loc_7610:
 push word [bp + 0x8]
status_loc_7613:
 lea ax, [bp + 0xff78]
status_loc_7617:
 push ax
status_loc_7618:
 call status_sprintf
status_loc_761b:
 add sp, 0x1a
status_loc_761e:
 push word [bp + 0x4]
status_loc_7621:
 push word [bp + 0x6]
status_loc_7624:
 lea ax, [bp + 0xff78]
status_loc_7628:
 push ax
status_loc_7629:
 call ui_write_string
status_loc_762c:
 mov_load sp, bp
status_loc_762e:
 pop bp
status_loc_762f:
 ret
%endif
%if STATUS_HELPERS_UNIT=0 || STATUS_HELPERS_UNIT=2
status_character_fill:
status_loc_7630:
 mov_load bx, sp
status_loc_7632:
 push di
status_loc_7633:
 mov cx, word [bx + 0x2]
status_loc_7636:
 mov di, word [bx + 0x4]
status_loc_7639:
 mov ax, word [bx + 0x6]
status_loc_763c:
 mov es, word [text_video_segment]
status_loc_7640:
 mov dx, word [text_cga_status_port]
status_loc_7644:
 cmp dx, 0x0
status_loc_7647:
 jnz status_loc_7651
status_loc_7649:
 stosb
status_loc_764a:
 inc di
status_loc_764b:
 loop status_loc_7649
status_loc_764d:
 pop di
status_loc_764e:
 ret 0x6
status_loc_7651:
 jcxz status_loc_764d
status_loc_7653:
 call status_cga_byte
status_loc_7656:
 inc di
status_loc_7657:
 loop status_loc_7653
status_loc_7659:
 jmp short status_loc_764d
%endif
%if STATUS_HELPERS_UNIT=0 || STATUS_HELPERS_UNIT=3
status_message:
status_loc_3226:
 push bp
status_loc_3227:
 mov_load bp, sp
status_loc_3229:
 call terminal_reset_status_fill
status_loc_322c:
 push word [bp + 0x4]
status_loc_322f:
 call program_strlen
status_loc_3232:
 pop bx
status_loc_3233:
 sub ax, word [ui_flow_region_cells]
status_loc_3237:
 neg ax
status_loc_3239:
 shr ax, 0x1
status_loc_323b:
 sub_load ah, ah
status_loc_323d:
 or ax, word [ui_flow_coordinate_base]
status_loc_3241:
 push ax
status_loc_3242:
 push word [reset_data_1f6c]
status_loc_3246:
 push word [bp + 0x4]
status_loc_3249:
 call ui_write_string
status_loc_324c:
 mov_load sp, bp
status_loc_324e:
 pop bp
status_loc_324f:
 ret
%endif
%if STATUS_HELPERS_UNIT=0 || STATUS_HELPERS_UNIT=4
status_cga_byte:
status_loc_7e0e:
 mov_load ah, al
status_loc_7e10:
 in al, dx
status_loc_7e11:
 test al, 0x1
status_loc_7e13:
 jnz status_loc_7e10
status_loc_7e15:
 cli
status_loc_7e16:
 in al, dx
status_loc_7e17:
 test al, 0x1
status_loc_7e19:
 jz status_loc_7e16
status_loc_7e1b:
 xchg al, ah
status_loc_7e1d:
 stosb
status_loc_7e1e:
 sti
status_loc_7e1f:
 ret
%endif
