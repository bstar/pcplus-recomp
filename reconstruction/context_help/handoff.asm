; Exact PCPlus2.01 resident57AE PCHELP descriptor producer.
; This is the external help handoff, not the56FE static command reference.
BITS 16
CPU 8086
%ifdef CONTEXT_HELP_OMF
SEGMENT _TEXT public class=CODE use16
global context_help_native
extern help_resolve,program_strcpy,program_get_ds,help_format_tail,help_execute
extern help_path_key,help_title,help_topic,help_ui_1d3e
extern help_normal,help_bold,help_reverse,help_mouse_x,help_mouse_y
extern help_tail_format,help_program_key
%else
ORG 0x57ae
%define help_resolve 0x353d
%define program_strcpy 0x8268
%define program_get_ds 0x76b0
%define help_format_tail 0x82b6
%define help_execute 0x433d
%define help_path_key 0x24ac
%define help_title 0x24b8
%define help_topic 0x397a
%define help_ui_1d3e 0x1d3e
%define help_normal 0x1d32
%define help_bold 0x1d34
%define help_reverse 0x1d38
%define help_mouse_x 0x2068
%define help_mouse_y 0x206a
%define help_tail_format 0x24c6
%define help_program_key 0x24d2
%endif
%include "encodings.inc"
context_help_native:
L_57ae: push bp
L_57af: mov_load bp,sp
L_57b1: sub sp,0x76
L_57b4: mov ax,help_path_key
L_57b7: push ax
L_57b8: call help_resolve
L_57bb: pop bx
L_57bc: push ax
L_57bd: lea ax,[bp-0x76]
L_57c0: push ax
L_57c1: call program_strcpy
L_57c4: pop bx
L_57c5: pop bx
L_57c6: lea ax,[bp-0x76]
L_57c9: mov [bp-0x16],ax
L_57cc: mov word [bp-0x14],help_title
L_57d1: mov ax,[help_topic]
L_57d4: mov [bp-0x12],ax
L_57d7: mov ax,[help_ui_1d3e]
L_57da: mov [bp-0x10],ax
L_57dd: mov ax,[help_normal]
L_57e0: mov [bp-0xe],ax
L_57e3: mov ax,[help_bold]
L_57e6: mov [bp-0xc],ax
L_57e9: mov ax,[help_reverse]
L_57ec: mov [bp-0xa],ax
L_57ef: mov ax,[help_mouse_x]
L_57f2: mov [bp-0x8],ax
L_57f5: mov ax,[help_mouse_y]
L_57f8: mov [bp-0x6],ax
L_57fb: call program_get_ds
L_57fe: mov [bp-0x2],ax
L_5801: lea ax,[bp-0x16]
L_5804: mov [bp-0x4],ax
L_5807: push word [bp-0x2]
L_580a: push ax
L_580b: mov ax,help_tail_format
L_580e: push ax
L_580f: lea ax,[bp-0x34]
L_5812: push ax
L_5813: call help_format_tail
L_5816: add sp,0x8
L_5819: sub_load ax,ax
L_581b: push ax
L_581c: push ax
L_581d: push ax
L_581e: lea ax,[bp-0x34]
L_5821: push ax
L_5822: mov ax,help_program_key
L_5825: push ax
L_5826: call help_resolve
L_5829: pop bx
L_582a: push ax
L_582b: call help_execute
L_582e: mov_load sp,bp
L_5830: pop bp
L_5831: ret
