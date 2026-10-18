; Maintained bounded wrapper, not original PCPlus code.
; Near C ABI: (source,destination,source_capacity,destination_capacity),
; all uint16 DS offsets/lengths; caller cleans8 bytes. DS=SS; DF clear.
; AX=expanded byte length,CF0 success. CF1 AX1extent/2missingNUL/3trailingcaret/
; 4destination too small/5overlap. No destination mutation on validation failure.
; Source capacity1..129; source/destination extents cannot wrap16-bit offsets.
; Success calls actual recovered4934. No UART, clock or DOS side effects.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global modem_expand_bounded
extern modem_expand_original
modem_expand_bounded:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 mov cx,[bp+8]
 jcxz .extent
 cmp cx,129
 ja .extent
 mov si,[bp+4]
 mov di,si
 add di,cx
 jc .extent
 mov ax,[bp+10]
 or ax,ax
 jz .extent
 add ax,[bp+6]
 jc .extent
 xor bx,bx
.scan:
 cmp si,di
 jae .unterminated
 lodsb
 or al,al
 jz .validated
 cmp al,94
 jne .count
 cmp si,di
 jae .trailing
 lodsb
 or al,al
 jz .trailing
 cmp al,94
 jne .count
 cmp si,di
 jae .count
 cmp byte [si],94
 jne .count
 inc si
.count:
 inc bx
 jmp .scan
.validated:
 mov ax,bx
 inc ax
 cmp ax,[bp+10]
 ja .small
 add ax,[bp+6] ; destination used end (extent validated above)
 mov dx,[bp+6]
 cmp dx,si
 jae .expand
 cmp [bp+4],ax
 jb .overlap
.expand:
 push word [bp+6]
 push word [bp+4]
 call modem_expand_original
 add sp,4
 mov ax,bx
 clc
 jmp .done
.extent:
 mov ax,1
 jmp .failed
.unterminated:
 mov ax,2
 jmp .failed
.trailing:
 mov ax,3
 jmp .failed
.small:
 mov ax,4
 jmp .failed
.overlap:
 mov ax,5
.failed:
 stc
.done:
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret
