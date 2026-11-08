; Owned startup-only full-parent loader/init/release diagnostic; no UART start.
BITS 16
CPU 8086
SEGMENT COMPILER_PROBE_CODE public align=16 class=FARCODE use16
GROUP COMPILER_PROBE_GROUP COMPILER_PROBE_CODE
extern _compiler_overlay_load,_compiler_overlay_init,_compiler_overlay_release,_compiler_overlay_info
extern _compiler_overlay_phase
extern _compiler_overlay_expected
report: dw 0x434f,1,0,0,0,0,0,0
%macro check 1
 inc word [cs:report+4]
 %1
 or ax,ax
 jnz failed
%endmacro
global terminal_compiler_overlay_probe
terminal_compiler_overlay_probe:
 push ds
 push es
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 check {call far _compiler_overlay_load}
 ; Duplicate load must refuse while the arena is owned.
 call far _compiler_overlay_load
 cmp ax,1
 jne failed
 inc word [cs:report+4]
 check {call far _compiler_overlay_init}
 xor ax,ax
 push ax
 call far _compiler_overlay_info
 add sp,2
 or ax,ax
 jnz failed
 inc word [cs:report+4]
 mov ax,3
 push ax
 call far _compiler_overlay_info
 add sp,2
 mov [cs:report+8],ax
 cmp ax,1
 jne failed
 inc word [cs:report+4]
 check {call far _compiler_overlay_release}
 call far _compiler_overlay_phase
 or ax,ax
 jnz failed
 inc word [cs:report+4]
 check {call far _compiler_overlay_load}
 check {call far _compiler_overlay_init}
 check {call far _compiler_overlay_release}
 jmp output
failed:
 mov [cs:report+6],ax
 or ax,ax
 jnz output
 mov word [cs:report+6],0xffff
output:
 call far _compiler_overlay_phase
 mov [cs:report+10],ax
 mov ax,seg _compiler_overlay_expected
 mov es,ax
 mov si,_compiler_overlay_expected
 mov ax,[es:si+4]
 mov [cs:report+12],ax
 mov ax,[es:si+16]
 mov [cs:report+14],ax
 push cs
 pop ds
 mov bx,1
 mov cx,16
 mov dx,report
 mov ah,0x40
 int 0x21
 mov ax,[cs:report+6]
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop es
 pop ds
 retf
