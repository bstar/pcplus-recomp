; Near Help-bank CRT-free DOS allocation adapters to resident mouse code.
BITS 16
CPU 8086
%macro entry 2
 global %1
 %1:
 push bp
 mov bp,sp
 %assign %%i %2-1
 %rep %2
  push word [bp+6+%%i*2]
  %assign %%i %%i-1
 %endrep
 call %1 %+ _target
 mov sp,bp
 pop bp
 retf
%endmacro
%ifdef HELP_OVERLAY_ROOT
SEGMENT NOTICEINPUT_CODE public align=16 class=FARCODE use16
%ifdef HELP_PARENT_FRAME
extern _help_parent_frame_allocate,_help_parent_frame_release
global _help_overlay_allocate_root,_help_overlay_release_root
_help_overlay_allocate_root: jmp far _help_parent_frame_allocate
_help_overlay_release_root: jmp far _help_parent_frame_release
extern _mouse_platform_allocate,_mouse_platform_release
%define _help_fallback_frame_allocate_target _mouse_platform_allocate
%define _help_fallback_frame_release_target _mouse_platform_release
entry _help_fallback_frame_allocate,1
entry _help_fallback_frame_release,2
%else
extern _mouse_platform_allocate,_mouse_platform_release
%define _help_overlay_allocate_root_target _mouse_platform_allocate
%define _help_overlay_release_root_target _mouse_platform_release
entry _help_overlay_allocate_root,1
entry _help_overlay_release_root,2
%endif
%else
SEGMENT HELP_OVL_CODE public align=16 class=FARCODE use16
extern _help_overlay_allocate_root,_help_overlay_release_root
%macro call_root 2
 global %1
 %1:
 push bp
 mov bp,sp
 %assign %%i %2-1
 %rep %2
  push word [bp+4+%%i*2]
  %assign %%i %%i-1
 %endrep
 call far %1 %+ _root
 mov sp,bp
 pop bp
 ret
%endmacro
call_root _help_overlay_allocate,1
call_root _help_overlay_release,2
%endif
