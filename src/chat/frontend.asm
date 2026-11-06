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
%ifdef CHAT_FOREGROUND_TEXT
 sbb ax,ax
 inc ax ; CF0 ->1, CF1 ->0, without retaining a branch island.
 jz .claimed
 extern terminal_macro_status
 mov [terminal_macro_status],ax ; Reset this session's overflow-bell latch.
.claimed:
%else
 mov ax,0
 jc .done
 inc ax
.done:
%endif
 retf
_chat_front_release:
%ifdef CHAT_FOREGROUND_TEXT
 ; The session admitted an empty FIFO. Anything still retained belongs to
 ; this Chat session; cancellation/failure must not turn it into BBS input.
 extern keyboard_bank_terminal_macro_cancel
 call far keyboard_bank_terminal_macro_cancel
 jmp far terminal_chat_storage_release
%else
 call far terminal_chat_storage_release
 retf
%endif
%macro bridge 2
global %1
%1:
 push bp
 push ax
%ifdef CHAT_FOREGROUND_TEXT
%if %2 = 0
 xor ax,ax
%else
 mov ax,%2
%endif
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
 push cs
 call _chat_front_event ; Same CONFIG_CODE segment; exact FAR return frame.
 add sp,4
 neg ax ; CF is exactly whether the C result was nonzero; POPs preserve it.
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 retf
%endif
