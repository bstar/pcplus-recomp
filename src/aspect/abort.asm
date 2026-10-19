; Exact PCPlus2.01 resident4EBC..4EFA. Retained REA
; analysis/pcplus-main/functions/0x14ebc.asm; original SHA256
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Native error abort uses the saved dispatcher10-byte near context and does
; not return: real longjmp restores BP/DI/SI/SP/IP, within the same CS, DS=SS.
; Optional position display retains tell/format/print dependencies. This routine
; does not own or roll back resources; the restored dispatcher closes them.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_ABORT_FLAT
ORG 0x4ebc
%define aspect_abort_display_position 0xe384
%define aspect_dispatch_stream 0x4b02
%define aspect_abort_tell 0x8ed8
%define aspect_abort_format 0x82b6
%define aspect_abort_format_string 0x495c
%define aspect_abort_print 0x427f
%define aspect_dispatch_exit_state 0xe378
%define aspect_dispatch_argument 0xe3ac
%define session_longjmp 0x9065
%else
SEGMENT _TEXT public class=CODE use16
global aspect_abort
extern aspect_abort_display_position,aspect_dispatch_stream
extern aspect_abort_tell,aspect_abort_format,aspect_abort_format_string,aspect_abort_print
extern aspect_dispatch_exit_state,aspect_dispatch_argument,session_longjmp
%endif
aspect_abort:
 push bp
 mov_load bp,sp
 sub sp,byte 0x52
 cmp word [aspect_abort_display_position],byte 0
 jz .unwind
 push word [aspect_dispatch_stream]
 call aspect_abort_tell
 pop bx
 push dx
 push ax
 mov ax,aspect_abort_format_string
 push ax
 lea ax,[bp-0x52]
 push ax
 call aspect_abort_format
 add sp,byte 8
 lea bx,[bp-0x52]
 call aspect_abort_print
.unwind:
 mov ax,0xffff
 mov [aspect_dispatch_exit_state],ax
 push ax
 mov ax,aspect_dispatch_argument
 push ax
 call session_longjmp
 pop bx
 pop bx
 mov_load sp,bp
 pop bp
 ret
