BITS 16
CPU 8086
GROUP DGROUP _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern program_break_install,program_break_restore,program_break_ignore
global ..start
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,0x351b
 int 0x21
 mov [initial_1b],bx
 mov [initial_1b+2],es
 mov al,0x23
 int 0x21
 mov [initial_23],bx
 mov [initial_23+2],es
 mov ax,0x3300
 int 0x21
 mov [initial_break],dl
 xor si,si
.flag:
 xor di,di
.initial:
 xor bp,bp
.child:
 mov dx,di
 mov ax,0x3301
 int 0x21
 mov [saved_sp],sp
 push word [flags+si]
 call program_break_install
 cmp sp,[saved_sp]
 jne failed
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne failed
 mov ax,0x351b
 int 0x21
 cmp bx,program_break_ignore
 jne failed
 mov ax,cs
 mov dx,es
 cmp ax,dx
 jne failed
 mov ax,0x3523
 int 0x21
 cmp bx,program_break_ignore
 jne failed
 mov ax,cs
 mov dx,es
 cmp ax,dx
 jne failed
 mov ax,0x3300
 int 0x21
 mov ax,[flags+si]
 test al,al
 jz .unchanged
 cmp dl,0
 jne failed
 jmp short .handler
.unchanged:
 mov ax,di
 cmp dl,al
 jne failed
.handler:
 stc
 std
 pushf
 pop ax
 mov [saved_flags],ax
 int 0x1b
 int 0x23
 pushf
 pop ax
 cld
 cmp ax,[saved_flags]
 jne failed
 ; Simulate the child's break policy and its two vector replacements.
 mov dx,bp
 mov ax,0x3301
 int 0x21
 push ds
 push cs
 pop ds
 mov dx,child_handler
 mov ax,0x251b
 int 0x21
 mov al,0x23
 int 0x21
 pop ds
 call program_break_restore
 cmp sp,[saved_sp]
 jne failed
 mov ax,0x351b
 int 0x21
 cmp bx,[initial_1b]
 jne failed
 mov ax,es
 cmp ax,[initial_1b+2]
 jne failed
 mov ax,0x3523
 int 0x21
 cmp bx,[initial_23]
 jne failed
 mov ax,es
 cmp ax,[initial_23+2]
 jne failed
 mov ax,0x3300
 int 0x21
 mov ax,[flags+si]
 test al,al
 jz .child_expected
 cmp di,1
 jne .child_expected
 cmp dl,1
 jne failed
 jmp short .next
.child_expected:
 mov ax,bp
 cmp dl,al
 jne failed
.next:
 inc word [cases]
 inc bp
 cmp bp,2
 jb .child
 inc di
 cmp di,2
 jb .initial
 add si,2
 cmp si,8
 jb .flag
 cmp word [cases],16
 jne failed
 mov byte [exit_status],0
 jmp short cleanup
failed:
 mov byte [exit_status],1
cleanup:
 cld
 push ds
 lds dx,[initial_1b]
 mov ax,0x251b
 int 0x21
 pop ds
 push ds
 lds dx,[initial_23]
 mov ax,0x2523
 int 0x21
 pop ds
 mov dl,[initial_break]
 mov ax,0x3301
 int 0x21
 mov ah,0x40
 mov bx,1
 mov cx,message_end-message
 mov dx,message
 int 0x21
 mov al,[exit_status]
 mov ah,0x4c
 int 0x21
child_handler: iret
SEGMENT _DATA public class=DATA use16
global program_break_original_1b,program_break_original_23,program_break_original_flag
program_break_original_1b: dd 0
program_break_original_23: dd 0
program_break_original_flag: db 0
initial_1b: dd 0
initial_23: dd 0
initial_break: db 0
saved_sp: dw 0
saved_flags: dw 0
flags: dw 0,1,0x100,0xffff
cases: dw 0
exit_status: db 1
message: db 'BREAK component returned; see exit status.',13,10
message_end:
SEGMENT STACK stack class=STACK use16
 resb 512
stack_top:
