; PCPlus2.01 resident CS:4B1F..4BFE, recovered from retained REA
; analysis/pcplus-main/functions/0x14b1f.asm. Original executable SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Exact native control loop, not a complete ASPECT interpreter. Backend symbols
; retain original call/return conventions; notably open consumes its two stack
; arguments and wait consumes one, while seek/close use caller cleanup; error consumes one argument.
; Entry stack: return, owner/context flag (DI), script argument (SI); RET4.
; DS=SS, near code/data; BP/SI/DI preserved. AX/BX/CX/DX/flags are volatile.
; The caller supplies a checked 215-word near handler table. This dispatcher
; bounds opcode <=D6 but does not validate individual table pointers or opcodes.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_DISPATCH_FLAT
ORG 0x4b1f
%define aspect_dispatch_initialize 0xc1d7
%define aspect_dispatch_probe 0x9048
%define aspect_dispatch_open 0xc21f
%define aspect_dispatch_service 0x4de9
%define aspect_dispatch_read 0x4cb4
%define aspect_dispatch_seek 0x853a
%define aspect_dispatch_wait 0x4c3c
%define aspect_dispatch_error 0x4efb
%define aspect_dispatch_invalid_command 0x4f88
%define aspect_dispatch_shutdown 0x4bff
%define aspect_dispatch_cleanup 0xc2eb
%define aspect_dispatch_close 0x8318
%define aspect_dispatch_finish 0xc273
%define aspect_dispatch_argument 0xe3ac
%define aspect_dispatch_paused 0x8e20
%define aspect_dispatch_wait_disabled 0xe382
%define aspect_dispatch_seek_enabled 0xe2f8
%define aspect_dispatch_stream 0x4b02
%define aspect_dispatch_handlers 0x4b08
%define aspect_dispatch_exit_state 0xe378
%define aspect_dispatch_next_script 0xe104
%else
SEGMENT _TEXT public class=CODE use16
global aspect_dispatch
extern aspect_dispatch_initialize,aspect_dispatch_probe,aspect_dispatch_open
extern aspect_dispatch_service,aspect_dispatch_read,aspect_dispatch_seek
extern aspect_dispatch_wait,aspect_dispatch_error,aspect_dispatch_invalid_command
extern aspect_dispatch_shutdown,aspect_dispatch_cleanup,aspect_dispatch_close
extern aspect_dispatch_finish
extern aspect_dispatch_argument,aspect_dispatch_paused,aspect_dispatch_wait_disabled
extern aspect_dispatch_seek_enabled,aspect_dispatch_stream,aspect_dispatch_handlers
extern aspect_dispatch_exit_state,aspect_dispatch_next_script
%ifdef ASPECT_RUNTIME_SERIAL
; Maintained raw-platform compatibility: without a renderer or pattern owner,
; leave queued bytes for explicit receive commands or the parent's ASIO return.
; Full admitted application and pattern-active paths retain native idle drain.
extern aspect_dispatch_idle_allowed
%endif
%endif
aspect_dispatch:
 push bp
 mov_load bp,sp
 sub sp,byte 2
 push di
 push si
 call aspect_dispatch_initialize
 mov si,[bp+6]
 mov di,[bp+4]
.restart:
 mov ax,aspect_dispatch_argument
 push ax
 call aspect_dispatch_probe
 pop bx
 or_load ax,ax
 jnz .opened
 push si
 push di
 call aspect_dispatch_open
 or_load ax,ax
 jnz .opened
 jmp near .finish
.opened:
 mov [bp+4],di
 jmp short .loop
.poll:
 call aspect_dispatch_service
 or_load ax,ax
 jnz .exit
 call aspect_dispatch_read
 mov_load si,ax
%ifdef ASPECT_RUNTIME_SERIAL
 call aspect_dispatch_idle_allowed
 or ax,ax
 jz .dispatch
%endif
 cmp word [aspect_dispatch_paused],byte 0
 jz .dispatch
 cmp si,0xc7
 jae .dispatch
 cmp word [aspect_dispatch_wait_disabled],byte 0
 jnz .dispatch
 cmp word [aspect_dispatch_seek_enabled],byte 0
 jz .wait
 mov ax,1
 push ax
 mov ax,0xffff
 cwd
 push dx
 push ax
 push word [aspect_dispatch_stream]
 call aspect_dispatch_seek
 add sp,byte 8
.wait:
 sub_load ax,ax
 push ax
 call aspect_dispatch_wait
 cmp word [aspect_dispatch_paused],byte 0
 jnz .wait
 cmp word [aspect_dispatch_seek_enabled],byte 0
 jnz .loop
.dispatch:
 cmp si,0xd6
 ja .outside
 shl si,1
 call word [si+aspect_dispatch_handlers]
 jmp short .loop
.outside:
 mov bx,[aspect_dispatch_stream]
 test byte [bx+6],0x10
 jz .invalid
 mov ax,0x6b
 push ax
 call aspect_dispatch_error
 jmp short .loop
.invalid:
 call aspect_dispatch_invalid_command
.loop:
 cmp word [aspect_dispatch_exit_state],byte 0
 jz .poll
.exit:
 or_load di,di
 jnz .owned
 cmp word [aspect_dispatch_exit_state],0x3e7
 jz .owned
 call aspect_dispatch_shutdown
 jmp short .close
.owned:
 sub_load di,di
.close:
 call aspect_dispatch_cleanup
 push word [aspect_dispatch_stream]
 call aspect_dispatch_close
 pop bx
 mov si,[aspect_dispatch_next_script]
 cmp word [aspect_dispatch_exit_state],0x3e7
 jnz .finish
 jmp near .restart
.finish:
 call aspect_dispatch_finish
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret 4
