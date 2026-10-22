; Actual DOS ABI probe. Screen/BIOS platform is explicitly maintained test code.
BITS 16
CPU 8086
GROUP DGROUP _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern program_notice_error,program_notice_message,program_notice_window
extern program_strlen,pcplus_seconds
global ..start
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,3
 int 0x10
 xor si,si
.entry:
 xor di,di
.mode:
 ; Empty the BIOS queue before this owned case.
.drain:
 mov ah,1
 int 0x16
 jz .empty
 xor ah,ah
 int 0x16
 jmp .drain
.empty:
 mov word [reads],0
 mov word [saved],0
 mov word [written],0
 mov word [restored],0
 mov word [clock_seen],0
 cmp di,0
 jne .no_key
 mov cx,0x2d78
 mov ah,5
 int 0x16
 or al,al
 jnz fail
.no_key:
 mov bp,0x9876
 mov [saved_sp],sp
 cmp si,0
 jne .message
 mov bx,message
 call program_notice_error
 jmp .returned
.message:
 cmp si,1
 jne .window
 mov ax,message
 push ax
 call program_notice_message
 jmp .returned
.window:
 mov ax,message
 push ax
 xor ax,ax
 push ax
 call program_notice_window
.returned:
 cmp bp,0x9876
 jne fail
 mov ax,ds
 mov bx,ss
 cmp ax,bx
 jne fail
 cmp sp,[saved_sp]
 jne fail
 cmp word [saved],1
 jne fail
 cmp word [written],1
 jne fail
 cmp word [restored],1
 jne fail
 cmp word [clock_seen],1
 jne fail
 mov ax,1
 sub ax,di
 cmp [reads],ax
 jne fail
 cmp word [program_notice_left],35
 jne fail
 cmp word [program_notice_right],45
 jne fail
 ; Every screen byte captured by the platform must have been restored.
 push si
 push di
 push ds
 push es
 mov ax,0xb800
 mov es,ax
 mov si,screen_copy
 xor di,di
 mov cx,2000
 repe cmpsw
 pop es
 pop ds
 pop di
 pop si
 jne fail
 inc word [cases]
 inc di
 cmp di,2
 jb .mode
 inc si
 cmp si,3
 jb .entry
 cmp word [cases],6
 jne fail
 mov dx,ok
 mov ah,9
 int 0x21
 mov ax,0x4c00
 int 0x21
fail:
 mov dx,bad
 mov ah,9
 int 0x21
 mov ax,0x4c01
 int 0x21
global program_notice_strlen,program_notice_clock
program_notice_strlen: jmp program_strlen
program_notice_clock:
 mov word [clock_seen],1
 jmp pcplus_seconds
global program_notice_bell,program_notice_tone
; Sound calls are explicit recording boundaries; no speaker claim.
program_notice_bell:
program_notice_tone:
 ret
global program_notice_save
program_notice_save:
 inc word [saved]
 push si
 push di
 push es
 push ds
 mov ax,ds
 mov es,ax
 mov di,screen_copy
 mov ax,0xb800
 mov ds,ax
 xor si,si
 mov cx,2000
 cld
 rep movsw
 pop ds
 pop es
 pop di
 pop si
 mov ax,screen_copy
 mov dx,ds
 ret
global program_notice_write
program_notice_write:
 push bp
 mov bp,sp
 push si
 push di
 push es
 inc word [written]
 mov si,[bp+4]
 cmp word [bp+6],0x70
 jne fail
 cmp word [bp+8],0x0a26
 jne fail
 mov ax,0xb800
 mov es,ax
 mov di,1676 ;row10,col38, byte offset
 mov ah,0x70
.next:
 lodsb
 or al,al
 jz .done
 stosw
 jmp .next
.done:
 pop es
 pop di
 pop si
 pop bp
 ret 6
global program_notice_poll,program_notice_read
program_notice_poll:
 mov ah,1
 int 0x16
 mov ax,0
 jz .empty
 inc ax
.empty:
 ret
program_notice_read:
 inc word [reads]
 xor ah,ah
 int 0x16
 ret
global program_notice_restore
program_notice_restore:
 push bp
 mov bp,sp
 cmp word [bp+4],program_notice_descriptor
 jne fail
 cmp word [bp+6],screen_copy
 jne fail
 mov ax,ds
 cmp [bp+8],ax
 jne fail
 inc word [restored]
 push si
 push di
 push es
 mov si,screen_copy
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov cx,2000
 rep movsw
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
global program_notice_descriptor,program_notice_left,program_notice_right,program_notice_attribute
program_notice_descriptor: dw 9
program_notice_left: dw 0
 dw 11
program_notice_right: dw 0
program_notice_attribute: dw 0x70
global transfer_dos_clock_sample
transfer_dos_clock_sample: times 4 dw 0
message: db 'HELLO',0
ok: db 'NOTICE 6 cases passed',13,10,'$'
bad: db 'NOTICE FAILED',13,10,'$'
cases: dw 0
saved_sp: dw 0
reads: dw 0
saved: dw 0
written: dw 0
restored: dw 0
clock_seen: dw 0
screen_copy: times 4000 db 0
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
