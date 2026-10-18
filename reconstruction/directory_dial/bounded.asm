; Maintained pure number expansion, no file/record lookup or original globals.
; near C(src,src_cap,codes250,dst,dst_cap,mode), caller removes12 bytes.
; mode0 literal,mode1 ASCIIuppercase+A..J replacement. Code contents not recursive.
; CF0 AXlength, CF1 AX1extent/2sourceNUL/3codeNUL/4overflow/5mode.
; Max source20 bytes and output60; validate/build scratch before destination write.
; DS=SS,DFclear; BP/BX/CX/DX/SI/DI preserved. Caller owns valid DS buffers.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global directory_dial_number_bounded
directory_dial_number_bounded:
 push bp
 mov bp,sp
 sub sp,68
 push bx
 push cx
 push dx
 push si
 push di
 cmp word [bp+14],1
 ja .mode_error
 mov cx,[bp+6]
 or cx,cx
 jz .extent
 cmp cx,21
 ja .extent
 mov si,[bp+4]
 mov bx,si
 add bx,cx
 jc .extent
 mov ax,[bp+12]
 or ax,ax
 jz .extent
 add ax,[bp+10]
 jc .extent
.source_nul:
 cmp byte [si],0
 je .source_ok
 inc si
 loop .source_nul
 mov ax,2
 jmp .error
.source_ok:
 cmp word [bp+14],0
 je .build
 mov bx,[bp+8]
 mov ax,bx
 add ax,250
 jc .extent
 mov dx,10
.code_slot:
 mov si,bx
 mov cx,25
.code_nul:
 cmp byte [si],0
 je .next_slot
 inc si
 loop .code_nul
 mov ax,3
 jmp .error
.next_slot:
 add bx,25
 dec dx
 jnz .code_slot
.build:
 mov si,[bp+4]
 lea di,[bp-68]
 xor dx,dx
.next:
 lodsb
 or al,al
 jz .ready
 cmp word [bp+14],0
 je .ordinary
 cmp al,'a'
 jb .upper
 cmp al,'z'
 ja .upper
 sub al,32
.upper:
 cmp al,'A'
 jb .ordinary
 cmp al,'J'
 ja .ordinary
 sub al,'A'
 xor ah,ah
 mov cx,25
 push dx
 mul cx
 pop dx
 add ax,[bp+8]
 push si
 mov si,ax
.code:
 lodsb
 or al,al
 jz .code_done
 cmp dx,60
 jae .code_overflow
 mov [di],al
 inc di
 inc dx
 jmp .code
.code_done:
 pop si
 jmp .next
.code_overflow:
 pop si
 jmp .overflow
.ordinary:
 cmp dx,60
 jae .overflow
 mov [di],al
 inc di
 inc dx
 jmp .next
.ready:
 mov byte [di],0
 mov ax,dx
 inc ax
 cmp ax,[bp+12]
 ja .overflow
 mov cx,ax
 lea si,[bp-68]
 mov di,[bp+10]
.copy:
 mov al,[si]
 mov [di],al
 inc si
 inc di
 loop .copy
 mov ax,dx
 clc
 jmp .done
.extent:
 mov ax,1
 jmp .error
.overflow:
 mov ax,4
 jmp .error
.mode_error:
 mov ax,5
.error:
 stc
.done:
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 ret

; OpenWatcom __cdecl convenience ABI: (number21,codes250,destination64,mode).
; Full AX status0success/1extent/2sourceNUL/3codeNUL/4overflow/5mode.
; Caller removes8 argument bytes. Only bounded.asm is needed for this API.
global _directory_number_expand,directory_number_expand
_directory_number_expand:
directory_number_expand:
 push bp
 mov bp,sp
 push bx
 push word [bp+10]
 mov ax,64
 push ax
 push word [bp+8]
 push word [bp+6]
 mov ax,21
 push ax
 push word [bp+4]
 call directory_dial_number_bounded
 mov bx,sp
 lea sp,[bx+12]
 jc .result
 xor ax,ax
.result:
 pop bx
 pop bp
 ret
