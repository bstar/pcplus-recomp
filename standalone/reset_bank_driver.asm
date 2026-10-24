; Root DS=SS owner stays distinct from the native reset bank. This diagnostic
; uses the real UART driver and a host-supplied512-byte binary sequence.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
extern stack_top,reset_bank_call,reset_bank_observation,reset_bank_wait,reset_bank_busy
extern uart_save_hardware_state,uart_restore_hardware_state,uart_disable,uart_enable
extern uart_install_interrupt,uart_restore_interrupt,uart_clear_receive_buffer
extern uart_set_baud_divisor,uart_set_line_control,uart_receive_byte,uart_try_write
extern uart_rx_count,uart_rx_dropped,uart_rx_read,uart_rx_write
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
 mov ax,ds
 mov es,ax
 mov di,canary
 mov ax,0xa55a
 mov cx,512
 rep stosw
 mov ax,0x350c
 int 0x21
 mov [old_vector],bx
 mov [old_vector+2],es
 call uart_save_hardware_state
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_install_interrupt
 add sp,2
 call uart_clear_receive_buffer
 xor ax,ax
 push ax
 mov ax,38400
 push ax
 call uart_set_baud_divisor
 add sp,4
 mov ax,1
 push ax
 mov ax,8
 push ax
 xor ax,ax
 push ax
 call uart_set_line_control
 add sp,6
 call uart_enable
 mov si,ready
.ready:
 lodsb
 or al,al
 jz .bank
.send:
 call uart_try_write
 jc .send
 jmp .ready
.bank:
 mov ax,seg reset_bank_wait
 mov es,ax
 mov word [es:reset_bank_wait],18
 mov ax,1
 call checked_call
 or ax,ax
 jnz failed
 mov [root_observation],ds
 mov [root_observation+2],ss
 mov [root_observation+4],sp
 pushf
 pop word [root_observation+6]
 mov ax,seg reset_bank_observation
 mov es,ax
 mov si,reset_bank_observation
 mov di,wide_observation
 mov cx,10
.observe:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .observe
 mov ax,ds
 cmp [wide_observation],ax
 je failed
 mov ax,[wide_observation]
 cmp ax,[wide_observation+2]
 jne failed
 cmp word [wide_observation+8],132
 jne failed
 cmp word [wide_observation+10],0
 jne failed
 cmp word [wide_observation+12],0
 jne failed
 cmp word [wide_observation+14],0
 jne failed
 cmp word [wide_observation+16],0
 jne failed
 cmp word [wide_observation+18],512
 jne failed
 cmp word [uart_rx_count],512
 jne failed
 xor si,si
.receive:
 call uart_receive_byte
 cmp ax,0xffff
 je failed
 mov bx,si
 cmp al,bl
 jne failed
.echo:
 call uart_try_write
 jc .echo
 inc si
 cmp si,512
 jb .receive
 cmp word [uart_rx_count],0
 jne failed
 cmp word [uart_rx_dropped],0
 jne failed
 mov ax,[uart_rx_read]
 cmp ax,[uart_rx_write]
 jne failed
 mov ax,seg reset_bank_wait
 mov es,ax
 mov word [es:reset_bank_wait],0
 mov cx,8
.cycles:
 push cx
 xor ax,ax
 call checked_call
 or ax,ax
 jnz failed
 mov ax,1
 call checked_call
 or ax,ax
 jnz failed
 pop cx
 loop .cycles
 mov ax,2
 call checked_call
 cmp ax,3
 jne failed
 xor ax,ax
 call checked_call
 or ax,ax
 jnz failed
 mov ax,3
 call checked_call
 or ax,ax
 jnz failed
 pushf
 cli
 call reset_bank_call
 pushf
 pop dx
 test dx,0x200
 jnz failed
 or word [refusal_bits],1
 cmp ax,1
 jne failed
 popf
 std
 call reset_bank_call
 cmp ax,1
 jne failed
 pushf
 pop ax
 test ax,0x400
 jz failed
 or word [refusal_bits],2
 cld
 push ds
 mov ax,0x5000
 mov ds,ax
 call reset_bank_call
 cmp ax,1
 pop ds
 jne failed
 or word [refusal_bits],4
 cmp word [checked_count],20
 jne failed
 mov si,canary
 mov cx,512
.canary:
 lodsw
 cmp ax,0xa55a
 jne failed
 loop .canary
 mov word [exit_status],0
 jmp finish
failed:
 cld
 sti
 mov word [exit_status],1
finish:
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_restore_interrupt
 add sp,2
 call uart_restore_hardware_state
 mov ax,0x350c
 int 0x21
 cmp bx,[old_vector]
 jne .bad_vector
 mov ax,es
 cmp ax,[old_vector+2]
 je .write
.bad_vector:
 mov word [exit_status],1
.write:
 mov dx,report_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .exit
 mov bx,ax
 mov dx,wide_observation
 mov cx,32
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.exit:
 mov ax,[exit_status]
 mov ah,0x4c
 int 0x21

checked_call:
 mov bx,0x1234
 mov cx,0x5678
 mov dx,0x9abc
 mov si,0x1357
 mov di,0x2468
 mov bp,0x4321
 push ax
 mov ax,0x7200
 mov es,ax
 pop ax
 pushf
 pop word [expected_flags]
 call reset_bank_call
 pushf
 pop word [returned_flags]
 inc word [checked_count]
 push ax
 mov ax,[expected_flags]
 cmp ax,[returned_flags]
 pop ax
 jne failed
 cmp bx,0x1234
 jne failed
 cmp cx,0x5678
 jne failed
 cmp dx,0x9abc
 jne failed
 cmp si,0x1357
 jne failed
 cmp di,0x2468
 jne failed
 cmp bp,0x4321
 jne failed
 push ax
 mov ax,es
 cmp ax,0x7200
 jne failed
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne failed
 cmp ax,DGROUP
 jne failed
 mov dx,0x9abc
 pop ax
 ret
SEGMENT _DATA public class=DATA use16
ready: db 'BANK-READY',13,0
report_name: db 'D:\BANK.BIN',0
old_vector: dw 0,0
exit_status: dw 1
wide_observation: times 10 dw 0
root_observation: times 4 dw 0
checked_count: dw 0
refusal_bits: dw 0
expected_flags: dw 0
returned_flags: dw 0
canary: times 1024 db 0
SEGMENT _BSS public align=16 class=BSS use16
SEGMENT STACK stack align=16 class=STACK use16
