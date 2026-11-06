; Banked register bridges into the parent-DS=SS experimental Chat core.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern terminal_chat_storage_acquire,terminal_chat_storage_release
extern _chat_front_event
global _chat_front_claim,_chat_front_release
_chat_front_claim:
 call far terminal_chat_storage_acquire
 mov ax,0
 jc .done
 inc ax
.done: retf
_chat_front_release:
 call far terminal_chat_storage_release
 retf
%macro bridge 2
global %1
%1:
 push bp
 push ax
%ifdef CHAT_FOREGROUND_TEXT
 mov ax,%2
 jmp chat_front_bridge_common
%else
 push bx
 push cx
 push dx
 push si
 push di
 push es
 push ax
 mov ax,%2
 push ax
 call far _chat_front_event
 add sp,4
 or ax,ax
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 jz %%no
 stc
 retf
%%no: clc
 retf
%endif
%endmacro
bridge terminal_chat_key_far,0
bridge terminal_chat_key_hold_far,1
bridge terminal_chat_receive_hold_far,2
bridge terminal_chat_receive_far,3
bridge terminal_chat_idle_far,4
bridge terminal_chat_stop_far,5
%ifdef CHAT_FOREGROUND_TEXT
; All six entries have the same preserved-register and carry ABI. Share the
; body rather than retaining six copies in the conventional-memory parent.
; At BP+12 is the caller's AX; AX itself is the selected event number.
chat_front_bridge_common:
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov bp,sp
 push word [bp+12]
 push ax
 call far _chat_front_event
 add sp,4
 or ax,ax
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 jz .no
 stc
 retf
.no:
 clc
 retf
%endif
