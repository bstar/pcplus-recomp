; Diagnostic-only, exact INT21 pass-through except selected DOS2C samples.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _notice_clock_hook,_notice_clock_enable,_notice_clock_disable
_notice_clock_hook:
 pushf
 cmp byte [cs:enabled],0
 je .chain
 cmp ah,0x2c
 jne .chain
 popf
 mov cx,0
 mov dx,0x0700
 iret
.chain:
 popf
 jmp far [cs:previous]
_notice_clock_enable:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [cs:previous],ax
 mov ax,[bp+6]
 mov [cs:previous+2],ax
 mov byte [cs:enabled],1
 pop bp
 ret
_notice_clock_disable:
 mov byte [cs:enabled],0
 ret
previous: dd 0
enabled: db 0
; Controlled tick fixtures are a diagnostic wrapper around the unmodified
; production atomic BIOS reader. Inactive calls tail directly to that reader.
extern _notice_actual_ticks
global _notice_ticks_native,_notice_ticks_enable,_notice_ticks_disable
_notice_ticks_native:
 cmp byte [cs:tick_enabled],0
 je .actual
 cmp byte [cs:tick_seen],0
 jne .next
 mov byte [cs:tick_seen],1
 mov ax,[cs:tick_first]
 mov dx,[cs:tick_first+2]
 ret
.next:
 mov ax,[cs:tick_next]
 mov dx,[cs:tick_next+2]
 ret
.actual:
 jmp _notice_actual_ticks
_notice_ticks_enable:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [cs:tick_first],ax
 mov ax,[bp+6]
 mov [cs:tick_first+2],ax
 mov ax,[bp+8]
 mov [cs:tick_next],ax
 mov ax,[bp+10]
 mov [cs:tick_next+2],ax
 mov byte [cs:tick_seen],0
 mov byte [cs:tick_enabled],1
 pop bp
 ret
_notice_ticks_disable:
 mov byte [cs:tick_enabled],0
 ret
tick_enabled: db 0
tick_seen: db 0
tick_first: dd 0
tick_next: dd 0
