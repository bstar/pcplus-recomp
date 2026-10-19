; Maintained mechanical cross-DS=SS bridge. This is not an ASIO capability.
%define RB_FRAME_BX 14
%define RB_FRAME_AX 16
%define RB_FRAME_FLAGS 18
%define RB_REENTRY 0xfffe
%define RB_INACTIVE 0xfffd
%define RB_ARGUMENT 0xfffc
%define RB_STACK 0xfffb
%define RB_GUARD_BYTES 16
%define RB_MIN_STACK 512
%define RB_SUSPENDED_MARGIN 512
%macro RB_SAVE 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
%endmacro
%macro RB_RETURN 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
%endmacro
