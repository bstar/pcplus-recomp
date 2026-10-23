; Parent-owned timer injects a controlled INT33 vector replacement only after
; recognizing the actual ASPECT callback and its PSP lineage. No callback call.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _retention_probe_install,_retention_probe_stop,_retention_probe_foreign
global _retention_sample
old1c: dw 0,0
old33: dw 0,0
parent_psp: dw 0
_retention_sample: times 12 dw 0
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
%endmacro
%macro restore 0
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
%endmacro
_retention_probe_install:
 push bp
 mov bp,sp
 save
 mov ax,[ss:bp+4]
 mov [cs:parent_psp],ax
 mov ax,0x351c
 int 0x21
 mov [cs:old1c],bx
 mov [cs:old1c+2],es
 push cs
 pop ds
 mov dx,timer
 mov ax,0x251c
 int 0x21
 restore
 pop bp
 ret
_retention_probe_stop:
 save
 mov dx,[cs:old1c]
 mov ds,[cs:old1c+2]
 mov ax,0x251c
 int 0x21
 cmp word [cs:_retention_sample],0x4e49
 jne .done
 mov dx,[cs:old33]
 mov ds,[cs:old33+2]
 mov ax,0x2533
 int 0x21
.done:
 restore
 ret
_retention_probe_foreign:
 iret
timer:
 save
 cmp word [cs:_retention_sample],0
 jne .done
 xor cx,cx
 xor dx,dx
 mov es,dx
 mov ax,0x14
 int 0x33
 push cx
 push dx
 push es
 mov ax,0x14
 int 0x33
 pop es
 pop dx
 pop cx
 cmp cx,11
 jne .done
 cmp dx,CHILD_CALLBACK
 jne .done
 cmp word [es:CHILD_CALLBACK-2],0xffff
 jne .done
 mov ax,es
 sub ax,CHILD_CODE+0x10
 jc .done
 mov bx,ax
 mov es,bx
 cmp word [es:0],0x20cd
 jne .done
 mov ax,[cs:parent_psp]
 cmp [es:0x16],ax
 jne .done
 mov [cs:_retention_sample+2],bx
 mov ax,bx
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [cs:_retention_sample+4],ax
 mov [cs:_retention_sample+6],dx
 mov ax,bx
 add ax,CHILD_CODE+0x10
 mov [cs:_retention_sample+8],ax
 mov word [cs:_retention_sample+10],CHILD_COUNT
 add bx,CHILD_DATA+0x10
 mov [cs:_retention_sample+12],bx
 mov ax,0x15
 int 0x33
 mov [cs:_retention_sample+22],bx
 mov ax,0x3533
 int 0x21
 mov [cs:old33],bx
 mov [cs:old33+2],es
 mov word [cs:_retention_sample],0x4e49
 push cs
 pop ds
 mov dx,_retention_probe_foreign
 mov ax,0x2533
 int 0x21
.done:
 restore
 jmp far [cs:old1c]
