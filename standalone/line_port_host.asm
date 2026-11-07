; Authored diagnostic: no actual UART, settings file or original UI dependency.
BITS 16
CPU 8086
GROUP DGROUP PADSEG _DATA STACK
SEGMENT _TEXT public class=CODE use16
extern line_port_key
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov si,vectors
 mov cx,vector_count
.next:
 push cx
 mov di,line_port_port
 mov ax,2
 mov [di],ax
 mov word [line_port_baud],4
 mov word [line_port_parity],0
 mov word [line_port_stop],1
 mov word [line_port_bits],8
 mov word [bell_count],0
 mov word [quiesce_count],0
 mov bp,0x1234
 mov [saved_sp],sp
 push word [cs:si]
 call line_port_key
 add sp,2
 cmp sp,[saved_sp]
 jne .fail
 cmp bp,0x1234
 jne .fail
 mov di,line_port_port
 mov bx,2
 mov cx,5
.compare:
 mov ax,[di]
 cmp ax,[cs:si+bx]
 jne .fail
 add di,2
 add bx,2
 loop .compare
 mov ax,[bell_count]
 cmp ax,[cs:si+12]
 jne .fail
 mov ax,[quiesce_count]
 cmp ax,[cs:si+14]
 jne .fail
 cmp ax,0
 je .advance
 cmp word [old_port],2
 jne .fail
.advance:
 add si,16
 pop cx
 dec cx
 jz .passed
 jmp .next
.passed:
 mov ax,0x4c00
 int 0x21
.fail:
 mov ax,0x4c01
 int 0x21

global line_port_bell,line_port_quiesce
line_port_bell:
 inc word [bell_count]
 ret
line_port_quiesce:
 mov ax,[line_port_port]
 mov [old_port],ax
 inc word [quiesce_count]
 ret

; key, expected port/baud/parity/stop/bits, bell count, quiesce count.
vectors:
%assign k 0
%rep 9
 dw 0x31+k,2,k,0,1,8,0,0
%assign k k+1
%endrep
%assign k 0
%rep 2
 dw 'N'+k*32,2,4,0,1,8,0,0
 dw 'O'+k*32,2,4,1,1,8,0,0
 dw 'E'+k*32,2,4,2,1,8,0,0
 dw 'M'+k*32,2,4,3,1,8,0,0
 dw 'S'+k*32,2,4,4,1,8,0,0
%assign k k+1
%endrep
 dw 0x7800,2,4,0,1,8,0,0
 dw 0x7900,2,4,0,2,8,0,0
 dw 0x7e00,2,4,0,1,7,0,0
 dw 0x7f00,2,4,0,1,8,0,0
 dw 0x1200,2,4,2,1,7,0,0
 dw 0x3100,2,4,0,1,8,0,0
%assign k 0
%rep 8
 dw 0x3b00+k*256,k,4,0,1,8,0,1
%assign k k+1
%endrep
%rep 1
 dw 0,2,4,0,1,8,1,0
 dw 27,2,4,0,1,8,1,0
 dw 0x1f00,2,4,0,1,8,1,0
 dw '0',2,4,0,1,8,1,0
 dw ':',2,4,0,1,8,1,0
 dw 0x4300,2,4,0,1,8,1,0
 dw 0xffff,2,4,0,1,8,1,0
%endrep
vector_count equ ($-vectors)/16

SEGMENT PADSEG public align=16 class=DATA use16
 times 128 db 0xa5
SEGMENT _DATA public class=DATA use16
; Explicit group-relative exports exercise a nonzero _DATA offset in DGROUP.
global line_port_port,line_port_baud,line_port_parity,line_port_stop,line_port_bits
line_port_port: dw 2
line_port_baud: dw 4
line_port_parity: dw 0
line_port_stop: dw 1
line_port_bits: dw 8
bell_count: dw 0
quiesce_count: dw 0
old_port: dw 0
saved_sp: dw 0
SEGMENT STACK stack align=16 class=STACK use16
 resb 1024
stack_top:
