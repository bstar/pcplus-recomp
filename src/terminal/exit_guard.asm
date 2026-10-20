; Final terminal lifetime check. No CRT startup, near calls or heap assumptions.
BITS 16
CPU 8086
%ifdef TERMINAL_EXIT_GUARD
GROUP DGROUP _DATA
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern process_psp,process_keep_paragraphs,process_busy
extern terminal_program_active,terminal_program_pending,terminal_aspect_active
extern hardware_active,terminal_exit_code
global terminal_exit_guard_begin,terminal_exit_guard_finish,terminal_exit_guard_hold
%ifdef TERMINAL_TRAPS
extern terminal_trap_phase
global terminal_exit_guard_mouse_held
terminal_exit_guard_mouse_held:
 or word [terminal_exit_guard_reason],4
 mov word [terminal_exit_code],14
 retf
%endif
%macro save 0
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
%endmacro
%macro restore 0
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
%endmacro
context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,DGROUP
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 test ax,0x200
 jz .bad
 clc
 ret
.bad:
 stc
 ret
; BX trusted PSP, DX immutable minimum paragraphs. AX current paragraph count.
extent:
 cmp bx,0x10
 jb .bad
 mov es,bx
 cmp word [es:0],0x20cd
 jne .bad
 dec bx
 mov es,bx
 inc bx
 cmp byte [es:0],'M'
 je .owner
 cmp byte [es:0],'Z'
 jne .bad
.owner:
 cmp [es:1],bx
 jne .bad
 mov ax,[es:3]
 cmp dx,0x10
 jb .bad
 cmp ax,dx
 jb .bad
 add ax,bx
 jc .bad
 mov ax,[es:3]
 clc
 ret
.bad:
 stc
 ret
; DX:BX target, SI IVT byte offset (or C0 for the CP/M gateway).
reference:
 shr bx,1
 shr bx,1
 shr bx,1
 shr bx,1
 add dx,bx
 cmp dx,[terminal_exit_guard_owner]
 jb .done
 cmp dx,[terminal_exit_guard_end]
 jae .done
 or word [terminal_exit_guard_reason],1
 mov ax,si
 shr ax,1
 shr ax,1
 mov [terminal_exit_guard_vector],ax
.done:
 ret
terminal_exit_guard_begin:
 save
 call context
 jc .invalid_context
 cmp word [terminal_exit_guard_valid],0
 jne .bad
 mov ah,0x62
 int 0x21
 cmp bx,[process_psp]
 jne .bad
 mov dx,[process_keep_paragraphs]
 call extent
 jc .bad
 mov [terminal_exit_guard_owner],bx
 mov [terminal_exit_guard_floor],dx
 mov word [terminal_exit_guard_valid],1
 pushf
 cli
 xor ax,ax
 mov es,ax
 mov ax,[es:0xc0]
 mov [terminal_exit_guard_gateway],ax
 mov ax,[es:0xc2]
 mov [terminal_exit_guard_gateway+2],ax
 xor ax,ax
 mov al,[es:0xc4]
 mov [terminal_exit_guard_gateway+4],ax
 popf
 restore
 clc
 retf
.bad:
 mov word [terminal_exit_code],15
.invalid_context:
 restore
 stc
 retf
terminal_exit_guard_finish:
 save
 call context
 jc terminal_exit_guard_hold
 cmp word [terminal_exit_guard_valid],1
 jne terminal_exit_guard_hold
%ifdef TERMINAL_EXIT_PROBE
 %if TERMINAL_EXIT_PROBE = 1
 mov ax,0x2560
 mov dx,terminal_exit_probe_isr
 push ds
 push cs
 pop ds
 int 0x21
 pop ds
 %elif TERMINAL_EXIT_PROBE = 2
 mov word [process_busy],1
 %elif TERMINAL_EXIT_PROBE = 3
 mov bx,[terminal_exit_guard_owner]
 inc bx ; Controlled foreign token; no DOS operation precedes restoration.
 mov ah,0x50
 int 0x21
 %endif
%endif
 mov bx,[terminal_exit_guard_owner]
 mov ah,0x50
 int 0x21
 mov ah,0x62
 int 0x21
 cmp bx,[terminal_exit_guard_owner]
 jne terminal_exit_guard_hold
 mov dx,[terminal_exit_guard_floor]
 call extent
 jc terminal_exit_guard_hold
 mov [terminal_exit_guard_paragraphs],ax
 add ax,bx
 mov [terminal_exit_guard_end],ax
 mov ax,[process_busy]
 or ax,[terminal_program_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_aspect_active]
%ifdef TERMINAL_TRAPS
 or ax,[terminal_trap_phase]
%endif
 xor dx,dx
 mov dl,[hardware_active]
 or ax,dx
 jz .vectors
 or word [terminal_exit_guard_reason],2
.vectors:
 ; Normalize every far IVT address, including noncanonical segment:offset
 ; spellings. A reference anywhere in the validated PSP block retains it.
 pushf
 cli
 xor ax,ax
 mov es,ax
 ; DOS can put a five-byte far JMP at0000:C0, over IVT slots30/31.
 ; An unchanged startup gateway is executable code, not two far pointers.
 ; Always audit its real target; changed bytes also get the ordinary scan.
 xor bp,bp
 cmp byte [es:0xc0],0xea
 jne .setup
 mov ax,[es:0xc0]
 cmp ax,[terminal_exit_guard_gateway]
 jne .gateway
 mov ax,[es:0xc2]
 cmp ax,[terminal_exit_guard_gateway+2]
 jne .gateway
 mov al,[es:0xc4]
 cmp al,[terminal_exit_guard_gateway+4]
 jne .gateway
 inc bp
.gateway:
 mov si,0xc0
 mov bx,[es:0xc1]
 mov dx,[es:0xc3]
 call reference
.setup:
 xor si,si
 mov cx,256
.vector:
 or bp,bp
 jz .ordinary
 cmp si,0xc0
 je .next
 cmp si,0xc4
 je .next
.ordinary:
 ; DOS4C/31 restores22/23/24 from this PSP before returning to the parent.
 ; Audit those effective targets, including a corrupted saved self-reference.
 cmp si,0x88
 jb .current
 cmp si,0x90
 ja .current
 push es
 mov bx,[terminal_exit_guard_owner]
 mov es,bx
 mov di,si
 sub di,0x7e ; IVT88/8C/90 -> PSP0A/0E/12.
 mov bx,[es:di]
 mov dx,[es:di+2]
 pop es
 call reference
 jmp short .next
.current:
 mov bx,[es:si]
 mov dx,[es:si+2]
 call reference
.next:
 add si,4
 loop .vector
 popf
%ifdef TERMINAL_EXIT_PROBE
 call report
%endif
 cmp word [terminal_exit_guard_reason],0
 jne .retain
 restore
 retf
.retain:
 mov dx,[terminal_exit_guard_paragraphs]
 mov ax,0x310f
%ifdef TERMINAL_TRAPS
 test word [terminal_exit_guard_reason],4
 jz .retain_status
 mov al,14
.retain_status:
%endif
 int 0x21
terminal_exit_guard_hold:
 sti
 hlt
 jmp terminal_exit_guard_hold
%ifdef TERMINAL_EXIT_PROBE
global terminal_exit_probe_isr
terminal_exit_probe_isr:
 push ax
 push ds
 mov ax,DGROUP
 mov ds,ax
 inc word [terminal_exit_probe_hits]
 pop ds
 pop ax
 iret
report:
 mov word [terminal_exit_probe_code_off],terminal_exit_probe_isr
 mov ax,cs
 mov [terminal_exit_probe_code_seg],ax
 mov word [terminal_exit_probe_data_off],terminal_exit_probe_hits
 mov ax,ds
 mov [terminal_exit_probe_data_seg],ax
 mov ah,0x62
 int 0x21
 mov [terminal_exit_probe_current_psp],bx
 mov dx,report_name
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc .done
 mov bx,ax
 mov dx,terminal_exit_probe_report
 mov cx,terminal_exit_probe_report_end-terminal_exit_probe_report
 mov ah,0x40
 int 0x21
 mov ah,0x3e
 int 0x21
.done:
 ret
%endif
SEGMENT _DATA public class=DATA use16
global terminal_exit_guard_owner,terminal_exit_guard_floor,terminal_exit_guard_valid
global terminal_exit_guard_paragraphs,terminal_exit_guard_reason,terminal_exit_guard_vector
terminal_exit_guard_valid: dw 0
terminal_exit_guard_end: dw 0
%ifdef TERMINAL_EXIT_PROBE
terminal_exit_probe_report:
 dw 0x5445,TERMINAL_EXIT_PROBE
%endif
terminal_exit_guard_owner: dw 0
terminal_exit_guard_floor: dw 0
terminal_exit_guard_paragraphs: dw 0
terminal_exit_guard_reason: dw 0
terminal_exit_guard_vector: dw 0xffff
%ifdef TERMINAL_EXIT_PROBE
terminal_exit_probe_code_off: dw 0
terminal_exit_probe_code_seg: dw 0
terminal_exit_probe_data_off: dw 0
terminal_exit_probe_data_seg: dw 0
terminal_exit_probe_current_psp: dw 0
global terminal_exit_probe_hits
terminal_exit_probe_hits: dw 0
%endif
terminal_exit_guard_gateway: times 3 dw 0
%ifdef TERMINAL_EXIT_PROBE
terminal_exit_probe_report_end:
report_name: db 'TERMEXIT.BIN',0
%endif
%endif
