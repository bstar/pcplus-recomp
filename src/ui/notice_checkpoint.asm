; Source-owned recovery frame for the notice's synchronous native call.
; Unlike small-model CRT longjmp, this frame is local to its actual code bank.
; All entries and _notice_call_native must share CS; DS=SS on entry. Callbacks
; in other banks must return through their proper far bridge before aborting.
; This is not an interrupt handler or an arbitrary-fault/nonlocal-unwind gate.
BITS 16
CPU 8086
%ifdef NOTICE_RESIDENT_CHECKPOINT
%define NOTICE_STATE_SEG ss
%else
%define NOTICE_STATE_SEG cs
%endif
%ifndef NOTICE_CHECKPOINT_SEGMENT
%define NOTICE_CHECKPOINT_SEGMENT _TEXT
%endif
%ifndef NOTICE_CHECKPOINT_CLASS
%define NOTICE_CHECKPOINT_CLASS CODE
%endif
SEGMENT NOTICE_CHECKPOINT_SEGMENT public class=NOTICE_CHECKPOINT_CLASS use16
extern _notice_call_native
global _notice_checkpoint_call,_notice_checkpoint_abort
global _notice_checkpoint_active
global _notice_checkpoint_discard
; Only an outer owner which has already discarded this frame may call here.
_notice_checkpoint_discard:
 mov word [NOTICE_STATE_SEG:ready],0
 ret
_notice_checkpoint_active:
 mov ax,[NOTICE_STATE_SEG:ready]
 ret
_notice_checkpoint_call:
%ifdef NOTICE_RESIDENT_CHECKPOINT
 mov ax,ss
 mov dx,DGROUP
 cmp ax,dx
 jne .busy
%endif
 cmp word [NOTICE_STATE_SEG:ready],0
 jne .busy
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 push ds
 pushf
 mov [NOTICE_STATE_SEG:saved_sp],sp
 mov [NOTICE_STATE_SEG:saved_ss],ss
 mov word [NOTICE_STATE_SEG:ready],1
 push word [bp+6]
 push word [bp+4]
 call _notice_call_native
 add sp,4
 xor ax,ax
 jmp short finish
.busy:
 mov ax,2
 ret
_notice_checkpoint_abort:
 cmp word [NOTICE_STATE_SEG:ready],1
 jne invalid
 ; Never restore a stale stack from a foreign child/interrupt context.
 mov ax,ss
 cmp ax,[NOTICE_STATE_SEG:saved_ss]
 jne invalid
 cli
 mov sp,[NOTICE_STATE_SEG:saved_sp]
 mov ax,1
finish:
 mov word [NOTICE_STATE_SEG:ready],0
 popf
 pop ds
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
invalid:
 ; Programming error: an abort outside its owned foreground frame cannot
 ; safely return to the caller. DOS termination is explicit, never success.
 mov ax,0x4c7f
 int 0x21
 hlt
 jmp short invalid
%ifdef NOTICE_RESIDENT_CHECKPOINT
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global notice_resident_checkpoint_state
notice_resident_checkpoint_state:
%endif
ready: dw 0
saved_sp: dw 0
saved_ss: dw 0
