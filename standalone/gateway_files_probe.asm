; Diagnostic-only startup entry and fixed three-word near-cdecl service.
BITS 16
CPU 8086
SEGMENT FILE_CODE public align=16 class=FARCODE use16
extern _gateway_files_probe
global terminal_gateway_probe
terminal_gateway_probe:
 call far _gateway_files_probe
 retf
global _gateway_probe_report
_gateway_probe_report:
 push bp
 mov bp,sp
 push ds
 push cs
 pop ds
 mov dx,name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 pop ds
 jc .failed
 mov bx,ax
 mov dx,[bp+6]
 mov cx,[bp+8]
 mov ah,0x40
 int 0x21
 jc .close_failed
 cmp ax,[bp+8]
 jne .close_failed
 mov ah,0x3e
 int 0x21
 jc .failed
 xor ax,ax
 jmp .done
.close_failed:
 mov ah,0x3e
 int 0x21
.failed:
 mov ax,1
.done:
 pop bp
 retf
name: db 'D:\GFRESULT.BIN',0
SEGMENT _TEXT public class=CODE use16
global _gateway_probe_near
_gateway_probe_near:
 push bp
 mov bp,sp
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 call word [bp+6]
 lea sp,[bp]
 pop bp
 retf
