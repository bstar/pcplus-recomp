; Original parent16 DDEE..DDF8: bounded integer operand0..127.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_CONFIG_OMF
SEGMENT _TEXT public class=CODE use16
global config_read_video_mode
extern config_bounded_integer
%else
ORG 0xddee
%define config_bounded_integer 0xdd68
%endif
config_read_video_mode:
 sub_load ax,ax
 push ax
 mov ax,127
 push ax
 call config_bounded_integer
 ret
