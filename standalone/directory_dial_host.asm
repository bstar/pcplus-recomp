; Independent synthetic DOS original quickdial + maintained literal/legacy checks.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern directory_dial_expand_original,_directory_number_expand
%macro push_value 1
 mov ax,%1
 push ax
%endmacro
%macro expand 1
 push_value %1
 push_value directory_dial_output
 push_value directory_dial_codes
 push_value directory_dial_input
 call _directory_number_expand
 add sp,8
%endmacro
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov word [directory_dial_codes],0x2c39 ;9,
 mov word [directory_dial_codes+25],0x302c ;,0
 mov word [directory_dial_records+25],0x3535
 mov byte [directory_dial_records+27],'b'
 push_value directory_dial_output
 xor ax,ax
 push ax
 call directory_dial_expand_original
 add sp,4
 cmp ax,1
 jne .fail
 cmp word [directory_dial_output],0x2c39
 jne .fail
 cmp word [directory_dial_output+2],0x3535
 jne .fail
 cmp word [directory_dial_output+4],0x302c
 jne .fail
 cmp word [directory_dial_output+6],0x302c
 jne .fail
 cmp byte [directory_dial_output+8],0
 jne .fail
 expand 0
 or ax,ax
 jnz .fail
 cmp word [directory_dial_output],0x3535
 jne .fail
 cmp word [directory_dial_output+2],0x0062
 jne .fail
 expand 1
 or ax,ax
 jnz .fail
 cmp word [directory_dial_output+2],0x302c
 jne .fail
 cmp byte [directory_dial_output+4],0
 jne .fail
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21
; Explicit synthetic in-memory record reader, not real directory IO.
global directory_dial_load_record
directory_dial_load_record:
 push bp
 mov bp,sp
 push si
 push di
 mov ax,[bp+4]
 dec ax
 mov dx,114
 mul dx
 add ax,directory_dial_records
 mov si,ax
 mov di,directory_dial_record
 mov cx,114
.copy:
 mov al,[si]
 mov [di],al
 inc si
 inc di
 loop .copy
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public align=16 class=DATA use16
global directory_dial_tokens,directory_dial_codes,directory_dial_record,directory_dial_records
global directory_dial_input,directory_dial_output
directory_dial_tokens: db 'a1b',0
 times 101 db 0
directory_dial_codes: times 250 db 0
directory_dial_record: times 114 db 0
directory_dial_records: times 22800 db 0
directory_dial_input: db '55b',0
 times 17 db 0
dw 0xa55a
directory_dial_output: times 64 db 0x5a
dw 0x5aa5
SEGMENT STACK stack align=16 class=STACK use16
resb 2048
stack_top:
