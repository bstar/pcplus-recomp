; Independent caller in a different CS from the small-model C/CRT caller.
BITS 16
CPU 8086
SEGMENT NOTICECODE public class=FARCODE use16
extern _notice_checkpoint_call,_notice_checkpoint_abort,_notice_checkpoint_active
extern _notice_checkpoint_peer
global _notice_checkpoint_probe,_notice_checkpoint_invalid,_notice_call_native
_notice_checkpoint_invalid:
 call _notice_checkpoint_abort
 retf ; unreachable; the test requires DOS exit127
_notice_checkpoint_probe:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push ds
 push es
 pushf
 mov ax,[bp+6] ; far cdecl mode
 mov [cs:mode],ax
 mov word [cs:failure],0
 mov [cs:entry_sp],sp
 mov [cs:entry_ds],ds
 mov bx,0x1234
 mov si,0x2345
 mov di,0x3456
 mov bp,0x4567
 mov dx,0x40
 mov es,dx
 ; Exercise both DF states. The native binding itself must clear DF.
 cld
 test ax,4
 jz .flags
 std
.flags:
 sti
 test ax,8
 jz .sample_flags
 cli
.sample_flags:
 pushf
 pop dx
 and dx,0x600
 mov [cs:entry_flags],dx
 push ax
 xor ax,ax
 push ax
 call _notice_checkpoint_call
 pushf
 pop dx
 add sp,4
 and dx,0x600
 cmp dx,[cs:entry_flags]
 je .flags_ok
 or word [cs:failure],1
.flags_ok:
 cld
 cmp sp,[cs:entry_sp]
 je .sp_ok
 or word [cs:failure],2
.sp_ok:
 cmp bx,0x1234
 jne .regs_bad
 cmp si,0x2345
 jne .regs_bad
 cmp di,0x3456
 jne .regs_bad
 cmp bp,0x4567
 jne .regs_bad
 mov dx,es
 cmp dx,0x40
 jne .regs_bad
 mov dx,ds
 cmp dx,[cs:entry_ds]
 je .regs_ok
.regs_bad:
 or word [cs:failure],4
.regs_ok:
 mov dx,[cs:mode]
 and dx,3
 jz .normal
 cmp ax,1
 je .return_ok
 jmp short .return_bad
.normal:
 or ax,ax
 jz .return_ok
.return_bad:
 or word [cs:failure],8
.return_ok:
 call _notice_checkpoint_active
 or ax,ax
 jz .inactive
 or word [cs:failure],16
.inactive:
 mov ax,[cs:failure]
 popf
 pop es
 pop ds
 pop di
 pop si
 pop bx
 pop bp
 retf
_notice_call_native:
 push bp
 mov bp,sp
 cld
 ; Call a far adapter in _TEXT which calls a near callback in that segment.
 push cs
 push word [bp+6]
 call far _notice_checkpoint_peer
 add sp,4
 mov dx,[bp+6]
 add dx,0x6000
 cmp ax,dx
 je .peer_ok
 or word [cs:failure],32
.peer_ok:
 call _notice_checkpoint_active
 cmp ax,1
 je .active
 or word [cs:failure],64
.active:
 mov ax,[bp+6]
 and ax,3
 cmp ax,2
 jne .nested_ok
 xor ax,ax
 push ax
 push ax
 call _notice_checkpoint_call
 add sp,4
 cmp ax,2
 je .nested_ok
 or word [cs:failure],128
.nested_ok:
 pop bp
 mov ax,[cs:mode]
 and ax,3
 jz .normal
 cmp ax,3
 jne .abort
 call deep
 or word [cs:failure],256 ; abort must bypass every intervening return
 ret
.abort:
 mov bx,0xabcd
 mov si,bx
 mov di,bx
 mov bp,bx
 mov es,bx
 mov ax,0x40
 mov ds,ax
 call _notice_checkpoint_abort
 or word [cs:failure],512
 ret
.normal:
 ret
deep:
 push ax
 push bx
 push cx
 push dx
 sub sp,40
 call _notice_call_native.abort
 or word [cs:failure],1024
 ret
mode: dw 0
failure: dw 0
entry_sp: dw 0
entry_ds: dw 0
entry_flags: dw 0
