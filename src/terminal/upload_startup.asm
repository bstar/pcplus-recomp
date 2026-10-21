; Maintained ordinary sender startup filter. Recovered sender stays unchanged.
; C/G/U/W must be the last byte before two quiet BIOS ticks; letters embedded
; in banner text or ANSI controls cannot consume the native attempt counter.
; NAK and CAN remain immediate. One native one-second request is bounded to
; 19 ticks, plus at most two ticks to settle a candidate at its boundary.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern terminal_transfer_fault
extern terminal_upload_startup_service_far,terminal_upload_startup_receive_far
GLOBAL terminal_upload_startup_byte
terminal_upload_startup_byte:
 push bp
 mov bp,sp
 sub sp,10 ;candidate word,start DWORD,candidate tick DWORD
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov word [bp-2],0xffff
 call clock
 mov [bp-6],ax
 mov [bp-4],dx
.poll:
 call far terminal_upload_startup_service_far
 cmp word [terminal_transfer_fault],0
 jne .timeout
 call far terminal_upload_startup_receive_far
 cmp ax,0xffff
 je .quiet
 cmp al,0x15
 je .done
 cmp al,0x18
 je .done
 mov bx,ax
 mov word [bp-2],0xffff
 mov ax,[terminal_upload_startup_ansi]
 ; Strings own ESC/ST. Elsewhere a fresh ESC cancels the incomplete ANSI
 ; sequence and begins another; its eventual C/G final is never a handshake.
 cmp ax,3
 je .string
 cmp ax,4
 je .string_escape
 cmp bl,0x1b
 jne .sequence
 mov word [terminal_upload_startup_ansi],1
 jmp .budget
.sequence:
 cmp ax,1
 je .escape
 cmp ax,2
 je .csi
 cmp ax,5
 je .normal
 jmp .candidate
.escape:
 cmp bl,'['
 je .begin_csi
 cmp bl,']'
 je .begin_string
 cmp bl,'P'
 je .begin_string
 cmp bl,'^'
 je .begin_string
 cmp bl,'_'
 je .begin_string
 cmp bl,'('
 je .charset
 cmp bl,')'
 je .charset
 jmp .normal
.begin_csi:
 mov word [terminal_upload_startup_ansi],2
 jmp .budget
.begin_string:
 mov word [terminal_upload_startup_ansi],3
 jmp .budget
.charset:
 mov word [terminal_upload_startup_ansi],5
 jmp .budget
.csi:
 cmp bl,0x40
 jb .budget
 cmp bl,0x7e
 ja .budget
 jmp .normal
.string:
 cmp bl,7
 je .normal
 cmp bl,0x1b
 jne .budget
 mov word [terminal_upload_startup_ansi],4
 jmp .budget
.string_escape:
 cmp bl,'\'
 je .normal
 cmp bl,0x1b
 je .budget
 mov word [terminal_upload_startup_ansi],3
 jmp .budget
.normal:
 mov word [terminal_upload_startup_ansi],0
 jmp .budget
.candidate:
 cmp bl,'C'
 je .save
 cmp bl,'G'
 je .save
 cmp bl,'U'
 je .save
 cmp bl,'W'
 jne .budget
.save:
 mov [bp-2],bx
 call clock
 mov [bp-10],ax
 mov [bp-8],dx
 jmp .budget
.quiet:
 cmp word [bp-2],0xffff
 je .budget
 lea si,[bp-10]
 call elapsed
 or dx,dx
 jnz .accepted
 cmp ax,2
 jb .budget
.accepted:
 mov ax,[bp-2]
 jmp .done
.budget:
 lea si,[bp-6]
 call elapsed
 or dx,dx
 jnz .timeout
 cmp ax,19
 jb .poll
 cmp word [bp-2],0xffff
 je .timeout
 cmp ax,21
 jb .poll
.timeout:
 mov ax,0xffff
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf
; Same atomic BDA snapshot/day normalization as the resident transfer owner.
; Keeping these tiny private helpers in this bank avoids resident code growth.
clock:
 push es
 pushf
 cli
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 mov dx,[es:0x6e]
 popf
 pop es
 ret
elapsed:
 call clock
 sub ax,[si]
 sbb dx,[si+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done:ret
SEGMENT _DATA public class=DATA use16
GLOBAL terminal_upload_startup_ansi
; Initialized in the loaded data image, retained across bounded native reads,
; and retired on every transfer notice before another admission can occur.
terminal_upload_startup_ansi: dw 0
