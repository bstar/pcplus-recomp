; Independent parent observer. No product addresses or test entrypoints.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _mouse_observer_prior,_mouse_observer_driver
global _mouse_observer_begin,_mouse_observer_end,_mouse_observer_stage,_mouse_observer_invoke
global _mouse_observer_registrations
_mouse_observer_prior:
 retf
_mouse_observer_begin:
 push bp
 mov bp,sp
 push bx
 push ds
 push es
 mov ax,[bp+4]
 mov [cs:mode],ax
 mov word [cs:stage],0
 mov word [cs:registrations],0
 mov ax,0x3533
 int 0x21
 mov [cs:old_mouse],bx
 mov [cs:old_mouse+2],es
 mov ax,0x351c
 int 0x21
 mov [cs:old_timer],bx
 mov [cs:old_timer+2],es
 push cs
 pop ds
 mov dx,_mouse_observer_driver
 mov ax,0x2533
 int 0x21
 mov dx,timer
 mov ax,0x251c
 int 0x21
 pop es
 pop ds
 pop bx
 pop bp
 ret
_mouse_observer_end:
 push ds
 mov dx,[cs:old_timer]
 mov ds,[cs:old_timer+2]
 mov ax,0x251c
 int 0x21
 mov dx,[cs:old_mouse]
 mov ds,[cs:old_mouse+2]
 mov ax,0x2533
 int 0x21
 pop ds
 ret
_mouse_observer_stage:
 mov ax,[cs:stage]
 ret
_mouse_observer_registrations:
 mov ax,[cs:registrations]
 ret
_mouse_observer_driver:
 cmp ax,0x15
 jne .callback
 cmp word [cs:mode],'U'
 jne .callback
 xor bx,bx ;Controlled unsupported storage API; production must use BIOS input.
 iret
.callback:
 cmp ax,0x0c
 jne .reset
 mov [cs:callback],dx
 mov [cs:callback+2],es
 jcxz .clear
 inc word [cs:registrations]
 jmp short .chain
.reset:
 cmp ax,0
 je .clear
 cmp ax,0x21
 je .clear
 cmp ax,0x17
 jne .chain
.clear:
 mov word [cs:callback],0
 mov word [cs:callback+2],0
.chain:
 jmp far [cs:old_mouse]

timer:
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
 mov ax,0xb800
 mov es,ax
 cmp word [cs:mode],'Q'
 jne .menu
 cmp word [cs:stage],0
 jne .done
 cmp byte [es:0],'Q'
 jne .done
 cmp byte [es:2],'S'
 jne .done
 cmp byte [es:4],'T'
 jne .done
 cmp byte [es:6],'O'
 jne .done
 cmp byte [es:8],'P'
 jne .done
 ; A deliberately damaged vector with the production callback still live.
 xor ax,ax
 mov es,ax
 mov word [es:0xcc],0
 mov word [es:0xce],0
 inc word [cs:stage]
 jmp short .done
.menu:
 cmp word [cs:mode],'S'
 jne .done
 cmp word [cs:stage],2
 jae .done
 mov ax,[cs:callback]
 or ax,[cs:callback+2]
 jz .done
 cmp word [es:2],0x1f50 ;PCPLUS Command Menu, actual video cells
 jne .done
 cmp word [es:4],0x1f43
 jne .done
 cmp word [es:20],0x1f6f
 jne .done
 cmp word [cs:stage],0
 jne .select
 mov ax,1
 xor si,si
 mov di,8 ;PRM y scale4 -> two native Down repetitions
 jmp short .emit
.select:
 cmp word [es:1130],0x7057 ;Write screen selected, not just menu entry
 jne .done
 mov ax,2 ;Actual registered callback's left-button event
 xor si,si
 mov di,8
.emit:
 mov bx,0x40
 mov ds,bx
 call far [cs:callback]
 inc word [cs:stage]
.done:
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
 jmp far [cs:old_timer]

_mouse_observer_invoke:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push ds
 push es
 pushf
 pop word [cs:saved_flags]
 mov ax,1
 mov si,16
 mov di,8
 mov bx,0x40
 mov ds,bx
 cli
 call far [ss:bp+4]
 mov bx,ds
 mov ax,1
 cmp bx,0x40
 je .returned
 xor ax,ax
.returned:
 push word [cs:saved_flags]
 popf
 pop es
 pop ds
 pop di
 pop si
 pop bx
 pop bp
 ret
old_mouse: dw 0,0
old_timer: dw 0,0
callback: dw 0,0
mode: dw 0
stage: dw 0
registrations: dw 0
saved_flags: dw 0
