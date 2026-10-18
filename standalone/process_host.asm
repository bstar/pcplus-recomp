BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern process_run,process_psp,process_keep_paragraphs,process_memory_released
extern process_minimum_paragraphs
extern process_busy
global process_test_start
..start:
process_test_start:
 mov dx,es
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov [process_psp],dx
 sub ax,dx
 mov bx,stack_top
 mov dx,bx
 mov cl,4
 shr bx,cl
 and dx,15
 jz .rounded
 inc bx
.rounded:
 add ax,bx
 mov [process_keep_paragraphs],ax
 mov [process_minimum_paragraphs],ax
 mov [retained],ax
 ; First child proves memory release, actual DOS EXEC and inherited environment.
 mov si,ordinary_tail
 call child
 or ax,ax
 jnz failed
 cmp word [result+4],37
 jne failed
 cmp word [process_memory_released],1
 jne failed
 mov ax,[process_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 cmp ax,[retained]
 jne failed
 ; Missing executable is an explicit DOS error, with no stale child status.
 mov ax,result
 push ax
 xor ax,ax
 push ax
 mov ax,missing_path
 push ax
 call process_run
 add sp,6
 cmp ax,3
 jne failed
 cmp word [result+2],2
 jne failed
 cmp word [result+4],0
 jne failed
 ; Empty optional tail, then the full126-byte command-tail capacity.
 xor si,si
 call child
 or ax,ax
 jnz failed
 mov si,maximum_tail
 call child
 or ax,ax
 jnz failed
 ; Bad CR and127-byte tail are rejected without a child or result mutation.
 mov word [result],0xcafe
 mov si,invalid_tail
 call child
 cmp ax,1
 jne failed
 cmp word [result],0xcafe
 jne failed
 mov si,too_long_tail
 call child
 cmp ax,1
 jne failed
 cmp word [result],0xcafe
 jne failed
 ; A genuine DOS resize error must not execute a child. Restore and recover.
 mov word [process_memory_released],0
 mov word [process_keep_paragraphs],0xffff
 xor si,si
 call child
 cmp ax,2
 jne failed
 cmp word [result+2],8
 jne failed
 mov ax,[retained]
 mov [process_keep_paragraphs],ax
 mov si,ordinary_tail
 call child
 or ax,ax
 jnz failed
 cmp word [result+4],37
 jne failed
 cmp word [guard_before],0xa55a
 jne failed
 cmp word [guard_after],0x5aa5
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
child:
 mov ax,result
 push ax
 push si
 mov ax,child_path
 push ax
 call process_run
 add sp,6
 ret

SEGMENT _DATA public align=16 class=DATA use16
retained: dw 0
child_path: db 'CHILD.COM',0
missing_path: db 'MISSING.COM',0
ordinary_tail: db ' ALPHA.TXT BETA.DAT',0
maximum_tail: times 126 db 'X'
 db 0
too_long_tail: times 127 db 'X'
 db 0
invalid_tail: db 'BAD',13,'TAIL',0
guard_before: dw 0xa55a
result: times 4 dw 0
guard_after: dw 0x5aa5
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
stack_top:
