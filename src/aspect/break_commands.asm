; Native PCPlus2.01 ASPECT BREAK/SET BREAK/FETCH BREAK and UI bracket.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Exact native instructions; hardware, calibrated delay and screen services external.
; DS=SS, nearRET; BP/SI/DI preserved, other registers/FLAGS volatile.
; No ownership, TEMT, cancellation, error unwind or foreign BREAK preservation.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_BREAK_FLAT
%if ASPECT_BREAK_UNIT=1
ORG 0x0401
%elif ASPECT_BREAK_UNIT=2
ORG 0xe67b
%elif ASPECT_BREAK_UNIT=3
ORG 0xe8a7
%elif ASPECT_BREAK_UNIT=4
ORG 0x6b42
%elif ASPECT_BREAK_UNIT=5
ORG 0x6b5a
%elif ASPECT_BREAK_UNIT=6
ORG 0x31bb
%endif
%if ASPECT_BREAK_UNIT!=1
%define aspect_break_native 0x0401
%endif
%if ASPECT_BREAK_UNIT!=4
%define aspect_break_cursor_pop 0x6b42
%endif
%if ASPECT_BREAK_UNIT!=5
%define aspect_break_cursor_push 0x6b5a
%endif
%if ASPECT_BREAK_UNIT!=6
%define aspect_break_notice 0x31bb
%endif
%define aspect_break_status_refresh 0x2fb8
%define aspect_break_notice_pointer 0x2074
%define aspect_break_lcr_port 0x8fee
%define aspect_break_in 0x829a
%define aspect_break_out 0x82a8
%define aspect_break_delay 0x6b72
%define aspect_break_delay_units 0x1d28
%define aspect_break_query_mode 0xe38e
%define aspect_break_operand 0xdd9c
%define aspect_break_store_integer 0xde3a
%define aspect_break_cursor_read 0x798e
%define aspect_break_cursor_write 0x6e78
%define aspect_break_cursor_current 0x7a36
%define aspect_break_cursor_floor 0x7a38
%define aspect_break_cursor_limit 0x7a4c
%define aspect_break_screen_end 0x3250
%define aspect_break_video_segment 0x7a84
%define aspect_break_video_offset 0x7a82
%define aspect_break_notice_disabled 0x1d46
%define aspect_break_notice_attribute 0x1f6e
%define aspect_break_screen_save 0x765c
%define aspect_break_screen_fill 0x6c20
%define aspect_break_screen_text 0x6bf0
%define aspect_break_wait_ticks 0x6b98
%define aspect_break_screen_restore 0x7682
%else
%ifdef ASPECT_BREAK_RUNTIME
%define ASPECT_BREAK_UNIT 7
SEGMENT _TEXT public class=CODE use16
global aspect_break_command,aspect_break_setting
extern aspect_break_native,aspect_break_status_refresh,aspect_break_delay_units
extern aspect_break_query_mode,aspect_break_operand,aspect_break_store_integer
%else
%define ASPECT_BREAK_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_break_native,aspect_break_command,aspect_break_setting
 global aspect_break_cursor_pop,aspect_break_cursor_push,aspect_break_notice
extern aspect_break_status_refresh,aspect_break_notice_pointer,aspect_break_lcr_port
extern aspect_break_in,aspect_break_out,aspect_break_delay,aspect_break_delay_units
extern aspect_break_query_mode,aspect_break_operand,aspect_break_store_integer
extern aspect_break_cursor_read,aspect_break_cursor_write
extern aspect_break_cursor_current,aspect_break_cursor_floor,aspect_break_cursor_limit
extern aspect_break_screen_end,aspect_break_video_segment,aspect_break_video_offset
extern aspect_break_notice_disabled,aspect_break_notice_attribute
extern aspect_break_screen_save,aspect_break_screen_fill,aspect_break_screen_text
extern aspect_break_wait_ticks,aspect_break_screen_restore
%endif
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=1
aspect_break_native:
 push si
 call aspect_break_cursor_push
 sub_load ax,ax
 push ax
 push word [aspect_break_notice_pointer]
 call aspect_break_notice
 pop bx
 pop bx
 push word [aspect_break_lcr_port]
 call aspect_break_in
 pop bx
 mov_load si,ax
 or si,byte 0x40
 push si
 push word [aspect_break_lcr_port]
 mov_load si,ax
 call aspect_break_out
 pop bx
 pop bx
 push word [aspect_break_delay_units]
 call aspect_break_delay
 mov_load ax,si
 and ax,0xbf
 push ax
 push word [aspect_break_lcr_port]
 call aspect_break_out
 pop bx
 pop bx
 call aspect_break_cursor_pop
 pop si
 ret
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=2 || ASPECT_BREAK_UNIT=7
aspect_break_command:
 call aspect_break_native
 jmp near aspect_break_status_refresh
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=3 || ASPECT_BREAK_UNIT=7
aspect_break_setting:
 cmp word [aspect_break_query_mode],0
 jnz .query
 call aspect_break_operand
 mov [aspect_break_delay_units],ax
 ret
.query:
 push word [aspect_break_delay_units]
 call aspect_break_store_integer
 ret
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=4
aspect_break_cursor_pop:
 mov bx,[aspect_break_cursor_current]
 cmp bx,[aspect_break_cursor_floor]
 jz .write
 sub bx,byte 2
.write:
 mov [aspect_break_cursor_current],bx
 push word [bx]
 call aspect_break_cursor_write
 ret
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=5
aspect_break_cursor_push:
 call aspect_break_cursor_read
 mov bx,[aspect_break_cursor_current]
 mov [bx],ax
 cmp bx,aspect_break_cursor_limit
 jnc .store
 add bx,byte 2
.store:
 mov [aspect_break_cursor_current],bx
 ret
%endif
%if ASPECT_BREAK_UNIT=0 || ASPECT_BREAK_UNIT=6
aspect_break_notice:
 push bp
 mov_load bp,sp
 sub sp,byte 0x1e
 push di
 push si
 mov di,[aspect_break_screen_end]
 sub di,byte 0x50
 mov_load ax,di
 sar di,1
 or di,[aspect_break_video_segment]
 mov_load si,ax
 add si,[aspect_break_video_offset]
 cmp word [aspect_break_notice_disabled],0
 jnz .done
 lea ax,[bp-0x1e]
 push ax
 push si
 mov ax,0xf
 push ax
 call aspect_break_screen_save
 mov ax,[aspect_break_notice_attribute]
 or ah,0x20
 push ax
 push si
 mov ax,0xf
 push ax
 call aspect_break_screen_fill
 lea ax,[di+1]
 push ax
 push word [aspect_break_notice_attribute]
 push word [bp+4]
 call aspect_break_screen_text
 cmp word [bp+6],0
 jz .done
 push word [bp+6]
 call aspect_break_wait_ticks
 lea ax,[bp-0x1e]
 push ax
 push si
 mov ax,0xf
 push ax
 call aspect_break_screen_restore
.done:
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
