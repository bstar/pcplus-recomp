; Original Elapsed Time control, overlay3:DB04..DB98 (149 bytes).
; REA ev_8162557c031b1b6b5dfb7d21e2fcadf0c2e9808010ef693a12cff0fa18e6ace5.
; Near cdecl DS=SS; preserves BP/SI. UI/clock/key services remain external.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0xdb04
%define elapsed_window_style 0x397a
%define elapsed_window_template 0x3294
%define elapsed_window_open 0x3fc7
%define elapsed_attribute 0x1f7c
%define elapsed_date 0x36d4
%define elapsed_print 0x6bf0
%define elapsed_carrier 0xaa5c
%define elapsed_online_text 0x2ea4
%define elapsed_offline_text 0x2ea6
%define elapsed_update 0x37a5
%define elapsed_time 0x498b
%define elapsed_duration 0x2c7c
%define elapsed_key_ready 0x6530
%define elapsed_read_key 0x64fe
%define elapsed_window_close 0x4015
%else
SEGMENT ELAPSED_NATIVE_CODE public align=16 class=FARCODE use16
extern elapsed_window_style,elapsed_window_template,elapsed_window_open
extern elapsed_attribute,elapsed_date,elapsed_print,elapsed_carrier
extern elapsed_online_text,elapsed_offline_text,elapsed_update,elapsed_time
extern elapsed_duration,elapsed_key_ready,elapsed_read_key,elapsed_window_close
global local_elapsed_db04
%endif
local_elapsed_db04:
 push bp
 db 0x8b,0xec ; MOV BP,SP, original direction-bit encoding.
 sub sp,8
 push si
 mov word [elapsed_window_style],10
 mov ax,elapsed_window_template
 push ax
 call elapsed_window_open
 pop bx
 db 0x8b,0xf0 ; MOV SI,AX, original direction-bit encoding.
 mov [bp-6],dx
 mov ax,0x0a2f
 push ax
 push word [elapsed_attribute]
 call elapsed_date
 push ax
 call elapsed_print
 call elapsed_carrier
 db 0x0b,0xc0 ; OR AX,AX, original direction-bit encoding.
 jz .offline
 mov ax,0x0c1b
 push ax
 push word [elapsed_attribute]
 push word [elapsed_online_text]
 jmp short .print
.offline:
 mov ax,0x0c1b
 push ax
 push word [elapsed_attribute]
 push word [elapsed_offline_text]
 jmp short .print
.update:
 call elapsed_carrier
 db 0x0b,0xc0 ; OR AX,AX, original direction-bit encoding.
 jz .time
 call elapsed_update
.time:
 mov ax,0x0a1e
 push ax
 push word [elapsed_attribute]
 db 0x2b,0xc0 ; SUB AX,AX, original direction-bit encoding.
 push ax
 call elapsed_time
 pop bx
 push ax
 call elapsed_print
 mov ax,0x0c33
 push ax
 push word [elapsed_attribute]
 mov ax,elapsed_duration
 push ax
.print:
 call elapsed_print
 call elapsed_key_ready
 db 0x0b,0xc0 ; OR AX,AX, original direction-bit encoding.
 jz .update
 call elapsed_read_key
 push word [bp-6]
 push si
 mov ax,elapsed_window_template
 push ax
 call elapsed_window_close
 add sp,6
 pop si
 db 0x8b,0xe5 ; MOV SP,BP, original direction-bit encoding.
 pop bp
 ret
