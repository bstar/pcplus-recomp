; Native viewport pane switching, CS:4816..4861.
BITS 16
CPU 8086
%ifdef VIEWPORT_OMF
SEGMENT _TEXT public class=CODE use16
global viewport_save_left,viewport_enter,viewport_save_right,viewport_leave
extern viewport_copy,ui_cga_blank,ui_cga_unblank,screen_viewport_active
%else
ORG 0x4816
%define viewport_copy 0x644c
%define ui_cga_blank 0x77be
%define ui_cga_unblank 0x77ae
%define screen_viewport_active 0x3256
%endif
%include "encodings.inc"
viewport_save_left:
 cmp word [screen_viewport_active],0
 jz short .done
 call ui_cga_blank
 sub_load ax,ax
 push ax
 call viewport_copy
 call ui_cga_unblank
.done: ret
viewport_enter:
 call viewport_save_right
 call ui_cga_blank
 mov ax,0x8000
 push ax
 call viewport_copy
 call ui_cga_unblank
 ret
viewport_save_right:
 cmp word [screen_viewport_active],0
 jnz short .done
 call ui_cga_blank
 mov ax,1
 push ax
 call viewport_copy
 call ui_cga_unblank
.done: ret
viewport_leave:
 call viewport_save_left
 call ui_cga_blank
 mov ax,0x8001
 push ax
 call viewport_copy
 call ui_cga_unblank
 ret
