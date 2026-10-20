; Explicit diagnostic foreground stimulus. Not present in normal trap builds.
BITS 16
CPU 8086
%ifdef TERMINAL_TRAP_PROBE
GROUP DGROUP _DATA
SEGMENT TRAP_CODE public align=16 class=FARCODE use16
extern terminal_trap_owner,terminal_trap_phase,terminal_trap_pending,terminal_trap_child
extern terminal_trap_flag,terminal_trap_originals,terminal_trap_error_context,terminal_trap_error_code
extern connection_state,hardware_active
global terminal_trap_probe_poll,terminal_trap_probe_closing,terminal_trap_probe_report
global terminal_trap_probe_foreign
terminal_trap_probe_poll:
 pushf
 push ax
 push bx
 push cx
 push dx
 push es
%if TERMINAL_TRAP_PROBE = 0
 jmp .done
%endif
 cmp word [probe_done],0
 jne .done
 cmp word [connection_state],6
 jne .done
 cmp byte [hardware_active],1
 jne .done
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 cmp word [probe_armed],0
 jne .elapsed
 mov [probe_tick],ax
 mov word [probe_armed],1
 jmp short .done
.elapsed:
 sub ax,[probe_tick]
 cmp ax,45
 jb .done
 mov word [probe_done],1
%if TERMINAL_TRAP_PROBE = 1
 int 0x1b
%elif TERMINAL_TRAP_PROBE = 2
 mov ah,5
 mov cx,0x2e03 ; BIOS Ctrl-C consumed by DOS's break-checking character read.
 int 0x16
 mov ah,0x08
 int 0x21
 mov [probe_kernel],ax
%elif TERMINAL_TRAP_PROBE = 3
 push di
 mov ax,0x0801
 mov di,12
 int 0x24 ; Declared synthetic critical event, not a faulty disk/device.
 mov [probe_kernel],ax
 pop di
%elif TERMINAL_TRAP_PROBE = 4
 push ds
 push cs
 pop ds
 mov dx,terminal_trap_probe_foreign
 mov ax,0x251b
 int 0x21
 pop ds
%endif
.done:
 pop es
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
terminal_trap_probe_foreign:
 push ax
 push ds
 mov ax,DGROUP
 mov ds,ax
 inc word [terminal_trap_probe_hits]
 pop ds
 pop ax
 iret
terminal_trap_probe_closing:
 push ax
 mov ax,[terminal_trap_phase]
 mov [probe_before_close],ax
 pop ax
 retf
terminal_trap_probe_report:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov di,probe_record
 push ds
 pop es
 mov ax,0x5452
 stosw
 mov ax,TERMINAL_TRAP_PROBE
 stosw
 mov ax,[terminal_trap_owner]
 stosw
 mov ax,[terminal_trap_phase]
 stosw
 mov ax,[terminal_trap_pending]
 stosw
 mov ax,[terminal_trap_child]
 stosw
 mov ax,[terminal_trap_flag]
 stosw
 mov ax,0x3300
 int 0x21
 xor ax,ax
 mov al,dl
 stosw
 mov ax,[terminal_trap_error_context]
 stosw
 mov ax,[terminal_trap_error_code]
 stosw
 mov ax,[probe_done]
 stosw
 mov ax,[probe_kernel]
 stosw
 mov si,terminal_trap_originals
 mov cx,6
 cld
 rep movsw
 xor ax,ax
 mov es,ax
 mov si,indices
 mov cx,3
.vectors:
 mov bx,[cs:si]
 mov ax,[es:bx]
 mov [di],ax
 mov ax,[es:bx+2]
 mov [di+2],ax
 add di,4
 add si,2
 loop .vectors
 mov word [di],terminal_trap_probe_foreign
 mov ax,cs
 mov [di+2],ax
 mov word [di+4],terminal_trap_probe_hits
 mov ax,ds
 mov [di+6],ax
 mov ax,[terminal_trap_probe_hits]
 mov [di+8],ax
 mov ax,[terminal_trap_owner]
 dec ax
 mov es,ax
 mov ax,[es:3]
 mov [di+10],ax
 mov ax,[probe_before_close]
 mov [di+12],ax
 mov dx,filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .done
 mov bx,ax
 mov dx,probe_record
 mov cx,62
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
indices: dw 0x1b*4,0x23*4,0x24*4
SEGMENT _DATA public class=DATA use16
global terminal_trap_probe_hits
terminal_trap_probe_hits: dw 0
probe_tick: dw 0
probe_armed: dw 0
probe_done: dw 0
probe_kernel: dw 0
probe_before_close: dw 0
probe_record: times 31 dw 0
filename: db 'TRAPWIT.BIN',0
%endif
