BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern _program_execute,process_psp,process_keep_paragraphs,process_minimum_paragraphs
global _small_code_
_small_code_:
..start:
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
 mov ax,result
 push ax
 mov ax,command
 push ax
 call _program_execute
 add sp,4
 mov [run_status],ax
 mov dx,result_file
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .failed
 mov bx,ax
 mov dx,result
 mov cx,8
 mov ah,0x40
 int 0x21
 jc .failed
 cmp ax,8
 jne .failed
 mov ah,0x3e
 int 0x21
 jc .failed
 mov ax,[run_status]
 or ax,ax
 jnz .failed
 cmp byte [result+5],0 ; Command processor's termination type, not nested child37.
 jne .failed
 cmp word [guard_before],0xa55a
 jne .failed
 cmp word [guard_after],0x5aa5
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
command: db 'CHILD.COM /Q SYNTH',0
result_file: db 'RESULT.OUT',0
run_status: dw 0
guard_before: dw 0xa55a
result: times 4 dw 0
guard_after: dw 0x5aa5
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
stack_top:
