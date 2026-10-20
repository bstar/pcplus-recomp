; CRT-free assembly parent. Retain every static segment before DOS allocation.
BITS 16
CPU 8086
%include "far_bridge.inc"
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
extern _bank_main,mouse_bank_bss_end
extern process_psp,process_keep_paragraphs,process_minimum_paragraphs,process_memory_released
global _small_code_
_small_code_:
..start:
 mov dx,es
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,terminal_stack_top
 sti
 cld
 mov es,ax
 mov di,mouse_bank_bss_start
 mov cx,mouse_bank_bss_end
 sub cx,di
 xor ax,ax
 rep stosb
 mov [process_psp],dx
 mov ax,ds
 sub ax,dx
 mov bx,terminal_stack_top
 add bx,15
 mov cl,4
 shr bx,cl
 add bx,ax
 mov [process_keep_paragraphs],bx
 mov [process_minimum_paragraphs],bx
 mov es,dx
 mov ah,0x4a
 int 0x21
 jc .failed
 mov word [process_memory_released],1
 call _bank_main
 mov ah,0x4c
 int 0x21
.failed:
 mov ax,0x4cfe
 int 0x21

; The diagnostic event injector itself lives beside the native far callback.
NEAR_CDECL_ENTRY _mouse_test_emit,3

global _test_size,_test_save,_test_exchange,_test_set_vector,_test_seed_key
global _test_bios_peek,_test_character,_test_owned_blocks,_test_keep
_test_size:
 push bx
 xor bx,bx
 mov ax,0x15
 int 0x33
 mov ax,bx
 pop bx
 ret
_test_save:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov dx,[bp+4]
 mov es,[bp+6]
 mov ax,0x16
 int 0x33
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_test_exchange:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov dx,[bp+4]
 mov es,[bp+6]
 mov cx,[bp+8]
 mov ax,0x14
 int 0x33
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_test_set_vector:
 push bp
 mov bp,sp
 push ds
 mov dx,[bp+4]
 mov ds,[bp+6]
 mov ax,0x2533
 int 0x21
 pop ds
 pop bp
 ret
_test_seed_key:
 mov ax,0x0500
 mov cx,0x256b
 int 0x16
 xor ah,ah
 ret
_test_bios_peek:
 mov ax,0x0100
 int 0x16
 ret
_test_character:
 push bp
 mov bp,sp
 mov dx,[bp+4]
 mov ah,2
 int 0x21
 pop bp
 ret
_test_keep:
 push es
 mov ax,[process_psp]
 dec ax
 mov es,ax
 mov ax,[es:3]
 pop es
 ret
_test_owned_blocks:
 push bx
 push si
 push di
 push es
 mov dx,[process_psp]
 mov ax,dx
 dec ax
 xor si,si
 mov cx,1024
.next:
 mov es,ax
 cmp byte [es:0],'M'
 je .valid
 cmp byte [es:0],'Z'
 jne .bad
.valid:
 cmp [es:1],dx
 jne .other
 inc si
.other:
 cmp byte [es:0],'Z'
 je .done
 mov bx,[es:3]
 inc bx
 jz .bad
 add ax,bx
 jc .bad
 loop .next
.bad:
 mov si,0xffff
.done:
 mov ax,si
 pop es
 pop di
 pop si
 pop bx
 ret
SEGMENT _BSS public align=16 class=BSS use16
global mouse_bank_bss_start
mouse_bank_bss_start:
SEGMENT _DATA public align=16 class=DATA use16
SEGMENT STACK stack align=16 class=STACK use16
 resb 8192
global terminal_stack_top
terminal_stack_top:
