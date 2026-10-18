BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern _transfer_crc16,_transfer_block_encode
global _transfer_blocks_dos_test
_transfer_blocks_dos_test:
 push bp
 push si
 push di
 mov si,digits
 mov di,transfer_block_input
 mov cx,9
.copy:
 mov al,[si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov ax,transfer_crc_result
 push ax
 mov ax,9
 push ax
 mov ax,transfer_block_input
 push ax
 call _transfer_crc16
 add sp,6
 or ax,ax
 jnz .fail
 cmp word [transfer_crc_result],0x31c3
 jne .fail
 mov ax,1029
 push ax
 mov ax,transfer_block_output
 push ax
 mov ax,1
 push ax
 mov ax,255
 push ax
 mov ax,128
 push ax
 mov ax,transfer_block_input
 push ax
 call _transfer_block_encode
 add sp,12
 or ax,ax
 jnz .fail
 cmp byte [transfer_block_output],1
 jne .fail
 cmp word [transfer_block_output+1],255
 jne .fail
 jmp short .done
.fail:
 mov ax,1
.done:
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
digits: db '123456789'
global transfer_block_input,transfer_block_output,transfer_crc_result
transfer_block_input: times 32768 db 0
 dw 0xa55a
transfer_block_output: times 1040 db 0xcc
 dw 0x5aa5
transfer_crc_result: dw 0xcccc
