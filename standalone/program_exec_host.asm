; Source-owned diagnostic startup and child. Original native EXEC core is real.
; Heap/UI/serial/process-search gaps trap; none is a no-op implementation.
BITS 16
CPU 8086
%ifdef PROGRAM_EXEC_CHILD
ORG 0x100
start:
 cmp byte [0x80],9
 jne .failed
 mov si,0x81
 mov di,expected_tail
 mov cx,9
 push ds
 pop es
 repe cmpsb
 jne .failed
 cmp byte [0x8a],13
 jne .failed
 mov ax,[0x2c]
 mov es,ax
 xor di,di
 mov si,expected_environment
 mov cx,13
 repe cmpsb
 jne .failed
 mov dx,result_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .failed
 mov bx,ax
 mov dx,0x80
 mov cx,11
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
 mov ax,0x4c25
 int 0x21
.failed:
 mov ax,0x4c63
 int 0x21
expected_tail: db ' /Q SYNTH'
expected_environment: db 'LABVAR=OWNED',0
result_name: db 'CHILD.OUT',0
%else
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern program_exec
..start:
 mov [cs:diagnostic_psp],es
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 ; Maintained diagnostic startup: release DOS maxalloc slack, retaining all
 ; source-built code/data/stack. The recovered EXEC helper does not do this.
 mov bx,ss
 sub bx,[cs:diagnostic_psp]
 mov ax,stack_top
 add ax,15
 mov cl,4
 shr ax,cl
 add bx,ax
 mov ax,[cs:diagnostic_psp]
 mov es,ax
 mov ax,0x4a00
 int 0x21
 jc failed
 mov word [program_exec_fcb1],program_fcb1
 mov word [program_exec_fcb2],program_fcb2
 mov byte [program_dos_major],5
 mov word [program_pair_low],0x1234
 mov word [program_pair_high],0x5678
 ; Dedicated aligned environment uses ordinary DOS ASCIIZ list semantics.
 mov si,environment_fixture
 mov di,0x5400
 mov cx,environment_fixture_end-environment_fixture
 push ds
 pop es
 rep movsb
 mov ax,0x5400
 push ax
 mov ax,tail_fixture
 push ax
 mov ax,child_name
 push ax
 xor ax,ax
 push ax
 call program_exec
 add sp,8
 cmp ax,37
 jne failed
 cmp word [program_pair_low],0x1234
 jne failed
 cmp word [program_pair_high],0x5678
 jne failed
 cmp word [program_exec_active],0
 jne failed
 ; Real DOS failure path: nonexistent owned-test filename must report errno2.
 mov ax,0x5400
 push ax
 mov ax,tail_fixture
 push ax
 mov ax,missing_name
 push ax
 xor ax,ax
 push ax
 call program_exec
 add sp,8
 cmp ax,0xffff
 jne failed
 cmp word [program_errno],2
 jne failed
 cmp byte [program_dos_error],2
 jne failed
 cmp word [program_exec_active],0
 jne failed
 cmp word [program_pair_low],0x1234
 jne failed
 cmp word [program_pair_high],0x5678
 jne failed
 mov ax,0x4c00
 int 0x21
failed:
 mov ax,0x4c01
 int 0x21
diagnostic_psp: dw 0
; Generated declarations give every unresolved service a fail-fast diagnostic
; boundary and every original DS cell a distinct source-owned storage alias.
%include "program_state.inc"
SEGMENT _DATA
child_name: db 'CHILD.COM',0
missing_name: db 'ABSENT.COM',0
tail_fixture: db 9,' /Q SYNTH',13
; DOS environment extension contains one executable name, owned test data only.
environment_fixture: db 'LABVAR=OWNED',0,0,1,0,'CHILD.COM',0
environment_fixture_end:
SEGMENT STACK stack align=16 class=STACK use16
 resb 4096
stack_top:
%endif
