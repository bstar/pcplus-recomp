; Recovered PCPlus2.01 2a6e..2a90; see docs/SCREEN_WIDTH_REQUEST.md.
BITS 16
CPU 8086
%ifdef WIDTH_REQUEST_OMF
SEGMENT _TEXT public class=CODE use16
global modes_width_request_native
extern reset_configured_wide,terminal_reset_native
%else
ORG 0x2a6e
%define reset_configured_wide 0x1d2e
%define terminal_reset_native 0x20a4
%endif
%include "encodings.inc"
modes_width_request_native:
 push bp
 mov_load bp,sp
 push si
 mov si,[reset_configured_wide]
 mov ax,[bp+4]
 mov [reset_configured_wide],ax
 sub_load ax,ax
 push ax
 call terminal_reset_native
 add sp,2
 mov [reset_configured_wide],si
 pop si
 mov_load sp,bp
 pop bp
 ret 2
