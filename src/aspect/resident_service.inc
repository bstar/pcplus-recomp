; Isolated source-owned far service diagnostic ABI, not an ASIO capability.
%define RS_FRAME_ES 0
%define RS_FRAME_DS 2
%define RS_FRAME_BP 4
%define RS_FRAME_DI 6
%define RS_FRAME_SI 8
%define RS_FRAME_DX 10
%define RS_FRAME_CX 12
%define RS_FRAME_BX 14
%define RS_FRAME_AX 16
%define RS_FRAME_FLAGS 18
%define RS_STACK_BYTES 1024
%define RS_MAGIC 0
%define RS_PARENT_PSP 2
%define RS_PARENT_DS 4
%define RS_ENTRY 6
%define RS_CHILD_PSP 10
%define RS_CHILD_DS 12
%define RS_CALLBACK 14
%define RS_BUSY 18
%define RS_SAVED_SS 20
%define RS_SAVED_SP 22
%define RS_FLAGS 24
%define RS_CALLS 26
%define RS_REFUSED 28
%define RS_FAILURES 30
%define RS_PARENT_CHECKS 32
%define RS_LAST_PSP 34
%define RS_INJECTED 36
%define RS_TIMER_PARENT 38
%define RS_CALLBACKS 40
%define RS_CHILD_CASES 42
%define RS_LOW_SP 44
%define RS_DESCRIPTOR_BYTES 46
%macro RS_SAVE_FRAME 0
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
%macro RS_RESTORE_FRAME 0
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
