; Exact PCPlus DOS time-of-day extraction: reusable original clock dependency.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef TRANSFER_UART_OMF
SEGMENT _TEXT public class=CODE use16
global pcplus_seconds,transfer_dos_time
extern transfer_dos_clock_sample
%else
%ifndef TRANSFER_UART_REGION
%define TRANSFER_UART_REGION 0
%endif
%define transfer_dos_clock_sample 0x8f02
%if TRANSFER_UART_REGION = 0
%define transfer_dos_time 0x778c
%endif
%endif
%ifidn __OUTPUT_FORMAT__,bin
%if TRANSFER_UART_REGION = 0
ORG 0x3323
%else
ORG 0x778c
%endif
%endif
%ifdef TRANSFER_UART_OMF
%define CLOCK_SECONDS
%define CLOCK_TIME
%else
%if TRANSFER_UART_REGION = 0
%define CLOCK_SECONDS
%else
%define CLOCK_TIME
%endif
%endif
%ifdef CLOCK_SECONDS
pcplus_seconds:
 mov ax,transfer_dos_clock_sample
 push ax
 call transfer_dos_time
 mov ax,[transfer_dos_clock_sample+6]
 ret
%endif
%ifdef CLOCK_TIME
transfer_dos_time:
 mov_load bx,sp
 mov bx,[bx+2]
 mov ah,0x2c
 int 0x21
 sub_load ah,ah
 mov_load al,dl
 mov [bx],ax
 mov_load al,ch
 mov [bx+2],ax
 mov_load al,cl
 mov [bx+4],ax
 mov_load al,dh
 mov [bx+6],ax
 ret 2
%endif
