; Standalone source-only DOS core diagnostic; no original resource inputs.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern _clipboard_self_test,_clipboard_test_checks,_clipboard_test_failures
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,terminal_stack_top
 sti
 cld
 call _clipboard_self_test
 push ax
 mov dx,result_path
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .failed
 mov bx,ax
 mov dx,_clipboard_test_checks
 mov cx,4
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,4
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc .failed
 pop ax
 or ax,ax
 jnz .failed
 mov dx,success
 mov ah,9
 int 0x21
 mov ax,0x4c00
 int 0x21
.close_failed:
 mov ah,0x3e
 int 0x21
.failed:
 mov dx,failure
 mov ah,9
 int 0x21
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public class=DATA use16
result_path: db 'CHECKS.BIN',0
success: db 'CLIPBOARD PASS',13,10,'$'
failure: db 'CLIPBOARD FAIL',13,10,'$'
SEGMENT _BSS public class=BSS use16
SEGMENT STACK stack class=STACK use16
resb 8192
global terminal_stack_top
terminal_stack_top:
