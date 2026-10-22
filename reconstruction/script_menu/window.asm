; Recovered native Alt-Z window, not original source. See provenance.json.
BITS 16
CPU 8086
%ifdef LOCAL_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global aspect_local_window
extern local_window_help_context
extern local_window_descriptor
extern local_window_box_attribute
extern local_window_keyboard_table
extern local_window_text
extern local_window_text_attribute
extern local_window_hook_enabled
extern local_window_hook_character
extern local_window_status
extern local_window_save
extern local_window_draw
extern local_window_keyboard_select
extern local_window_write
extern local_window_format
extern local_window_status_draw
extern local_window_key_poll
extern local_window_key_read
extern local_window_restore
%else
ORG 0x56fe
%define local_window_help_context 0x397a
%define local_window_descriptor 0x32b2
%define local_window_box_attribute 0x1f64
%define local_window_keyboard_table 0x232c
%define local_window_text 0x232a
%define local_window_text_attribute 0x1f66
%define local_window_hook_enabled 0x1d6e
%define local_window_hook_character 0x1d70
%define local_window_status 0x2328
%define local_window_save 0x3fc7
%define local_window_draw 0x4056
%define local_window_keyboard_select 0x780e
%define local_window_write 0x6bf0
%define local_window_format 0x75e8
%define local_window_status_draw 0x3226
%define local_window_key_poll 0x6530
%define local_window_key_read 0x64fe
%define local_window_restore 0x4015
%endif
%include "encodings.inc"
aspect_local_window: push bp
local_window_at_56ff: mov_load bp,sp
local_window_at_5701: sub sp,0x8
local_window_at_5704: push di
local_window_at_5705: push si
local_window_at_5706: mov word [local_window_help_context],0x29
local_window_at_570c: mov ax,local_window_descriptor
local_window_at_570f: push ax
local_window_at_5710: call local_window_save
local_window_at_5713: pop bx
local_window_at_5714: mov_load di,ax
local_window_at_5716: mov [bp-0x6],dx
local_window_at_5719: mov ax,0x201
local_window_at_571c: push ax
local_window_at_571d: mov ax,0x44e
local_window_at_5720: push ax
local_window_at_5721: push word [local_window_box_attribute]
local_window_at_5725: call local_window_draw
local_window_at_5728: mov ax,local_window_keyboard_table
local_window_at_572b: push ax
local_window_at_572c: call local_window_keyboard_select
local_window_at_572f: mov ax,0x1536
local_window_at_5732: push ax
local_window_at_5733: push word [local_window_text_attribute]
local_window_at_5737: push word [local_window_text]
local_window_at_573b: call local_window_write
local_window_at_573e: cmp word [local_window_hook_enabled],0x0
local_window_at_5743: jz short local_window_at_575c
local_window_at_5745: mov al,[local_window_hook_character]
local_window_at_5748: cbw
local_window_at_5749: push ax
local_window_at_574a: mov ax,0x4eb6
local_window_at_574d: push ax
local_window_at_574e: push word [local_window_box_attribute]
local_window_at_5752: mov ax,0x154c
local_window_at_5755: push ax
local_window_at_5756: call local_window_format
local_window_at_5759: add sp,0x8
local_window_at_575c: push word [local_window_status]
local_window_at_5760: call local_window_status_draw
local_window_at_5763: pop bx
local_window_at_5764: call local_window_key_poll
local_window_at_5767: mov_load si,ax
local_window_at_5769: or_load si,si
local_window_at_576b: jz short local_window_at_5764
local_window_at_576d: and si,0xff
local_window_at_5771: jz short local_window_at_579a
local_window_at_5773: cmp si,0xe0
local_window_at_5777: jz short local_window_at_579a
local_window_at_5779: cmp si,0x1c
local_window_at_577c: jz short local_window_at_579a
local_window_at_577e: cmp si,0x1d
local_window_at_5781: jz short local_window_at_579a
local_window_at_5783: cmp si,0x1f
local_window_at_5786: jz short local_window_at_579a
local_window_at_5788: cmp word [local_window_hook_enabled],0x0
local_window_at_578d: jz short local_window_at_5797
local_window_at_578f: mov al,[local_window_hook_character]
local_window_at_5792: cbw
local_window_at_5793: cmp_load ax,si
local_window_at_5795: jz short local_window_at_579a
local_window_at_5797: call local_window_key_read
local_window_at_579a: push word [bp-0x6]
local_window_at_579d: push di
local_window_at_579e: mov ax,local_window_descriptor
local_window_at_57a1: push ax
local_window_at_57a2: call local_window_restore
local_window_at_57a5: add sp,0x6
local_window_at_57a8: pop si
local_window_at_57a9: pop di
local_window_at_57aa: mov_load sp,bp
local_window_at_57ac: pop bp
local_window_at_57ad: ret
