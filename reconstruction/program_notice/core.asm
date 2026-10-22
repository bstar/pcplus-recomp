; Exact PCPlus2.01 timed notice controller. See provenance.json.
; DS=SS. BX message wrapper; other entries RET2 and RET4 respectively.
BITS 16
CPU 8086
%ifdef PROGRAM_NOTICE_OMF
SEGMENT _TEXT public class=CODE use16
global program_notice_error,program_notice_message,program_notice_window
extern program_notice_strlen,program_notice_clock,program_notice_bell
extern program_notice_tone,program_notice_save,program_notice_write
extern program_notice_poll,program_notice_read,program_notice_restore
extern program_notice_left,program_notice_right,program_notice_attribute
extern program_notice_descriptor
%else
ORG 0x427f
%define program_notice_strlen 0x8d18
%define program_notice_clock 0x3323
%define program_notice_bell 0x376d
%define program_notice_tone 0x3778
%define program_notice_save 0x3fc7
%define program_notice_write 0x6bf0
%define program_notice_poll 0x6530
%define program_notice_read 0x64fe
%define program_notice_restore 0x4015
%define program_notice_left 0x330e
%define program_notice_right 0x3312
%define program_notice_attribute 0x1f76
%define program_notice_descriptor 0x330c
%endif
%include "encodings.inc"
program_notice_error:
 push bx
 mov ax,1
 push ax
 call program_notice_window
 ret
program_notice_message:
 push bp
 mov_load bp,sp
 push word [bp+4]
 sub_load ax,ax
 push ax
 call program_notice_window
 mov_load sp,bp
 pop bp
 ret 2
program_notice_window:
 push bp
 mov_load bp,sp
 sub sp,byte 12
 push di
 push si
 push word [bp+6]
 call program_notice_strlen
 pop bx
 mov_load si,ax
 cwd
 sub_load ax,dx
 sar ax,1
 sub ax,strict word 40
 neg ax
 mov [bp-4],ax
 mov_load cx,ax
 sub ax,strict word 3
 mov [program_notice_left],ax
 add_load cx,si
 inc cx
 inc cx
 mov [program_notice_right],cx
 mov si,3
 call program_notice_clock
 mov [bp-2],ax
 cmp word [bp+4],byte 0
 je .tone
 call program_notice_bell
 jmp short .save
.tone:
 call program_notice_tone
.save:
 mov ax,program_notice_descriptor
 push ax
 call program_notice_save
 pop bx
 mov [bp-12],ax
 mov [bp-10],dx
 mov ax,[bp-4]
 or ah,10
 push ax
 push word [program_notice_attribute]
 push word [bp+6]
 call program_notice_write
 mov di,[bp-2]
 jmp short .poll
.wait:
 or_load si,si
 jz .finish
 call program_notice_clock
 cmp_load ax,di
 jz .poll
 call program_notice_clock
 mov_load di,ax
 dec si
.poll:
 call program_notice_poll
 or_load ax,ax
 jz .wait
.finish:
 call program_notice_poll
 or_load ax,ax
 jz .restore
 call program_notice_read
.restore:
 push word [bp-10]
 push word [bp-12]
 mov ax,program_notice_descriptor
 push ax
 call program_notice_restore
 add sp,byte 6
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret 4
