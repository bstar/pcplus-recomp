; Module-local FAR platform services, no DATA/CRT/private stack. DS=SS.
BITS 16
CPU 8086
SEGMENT CHAT_CODE public align=16 class=FARCODE use16
global _chat_timing_flags,_chat_timing_ticks,_chat_timing_one
global chat_timing_loop,chat_timing_complete
_chat_timing_flags:
 pushf
 pop ax
 retf
_chat_timing_ticks:
 pushf
 cli
 push es
 xor ax,ax
 mov es,ax
 mov ax,[es:0x46c]
 mov dx,[es:0x46e]
 pop es
 popf
 retf
_chat_timing_one:
 push bp
 mov bp,sp
 push bx
 push es
 xor ax,ax
 push ax ; Original6B72's zero comparison word, caller-owned on DS=SS stack.
 lea bx,[bp-6]
 mov ax,ds
 mov es,ax
 mov cx,[ss:bp+6]
chat_timing_loop:
 sub cx,byte 1
 adc ax,strict word 0
 cmp cx,[es:bx]
 jne chat_timing_loop
chat_timing_complete:
 add sp,2
 pop es
 pop bx
 pop bp
 retf
 align 2,db 0 ; Keep the empty aligned DATA group from requiring minalloc1.
