; Parent-only startup frontend. No child/compiler RPC admission yet.
BITS 16
CPU 8086
SEGMENT COMPILER_FRONT_CODE public align=16 class=FARCODE use16
GROUP COMPILER_FRONT_GROUP COMPILER_FRONT_CODE
extern process_psp,hardware_active,vector_active
extern _redisplay_active,_command_menu_active,_redisplay_live_ready
extern _line_overlay_state,compiler_overlay_owner_kind,compiler_overlay_active_expected
extern compiler_overlay_open,compiler_overlay_close
%define phase _line_overlay_state
%define stage _line_overlay_state+2
%define handle _line_overlay_state+4
%define at _line_overlay_state+6
%define fix _line_overlay_state+8
%define busy _line_overlay_state+10
%define fatal _line_overlay_state+12
%define crc _line_overlay_state+14
%define dirty _line_overlay_state+30
extern _line_port_front_poll
extern _compiler_lease_init,_compiler_lease_info
; Six shared-loader words follow magic/version, then retained paragraph cut.
global _compiler_overlay_expected
_compiler_overlay_expected: dw 0x434b,1,0,0,0,0,0,0,0
nonce: dw 0
%macro entry 1
global _compiler_overlay_%1
_compiler_overlay_%1:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 call context
 or ax,ax
 jnz %%valid
 mov ax,2
 jmp leave
%%valid:
%endmacro
leave:
 lea sp,[bp-14]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
context:
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 mov dx,seg process_psp
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 cmp byte [hardware_active],0
 jne .bad
 cmp byte [vector_active],0
 jne .bad
 mov ax,[_redisplay_active]
 or ax,[_command_menu_active]
 or ax,[_redisplay_live_ready]
 jnz .bad
 mov ah,0x51
 int 0x21
 cmp bx,[process_psp]
 jne .bad
 dec bx
 mov es,bx
 mov al,[es:0]
 cmp al,'M'
 je .type
 cmp al,'Z'
 jne .bad
.type:
 inc bx
 cmp [es:1],bx
 jne .bad
 mov ax,[cs:_compiler_overlay_expected+16]
 cmp ax,[es:3]
 jae .bad
 mov ax,1
 ret
.bad:xor ax,ax
 ret
entry load
 call start
 cmp ax,1
 je leave
 or ax,ax
 jnz .failed
 mov cx,64
.poll:
 call far _line_port_front_poll
 call far _compiler_overlay_phase
 cmp ax,2
 je .ready
 cmp ax,1
 jne .failed
 loop .poll
.failed:
 call release_raw
 mov ax,4
 jmp leave
.ready:
 xor ax,ax
 jmp leave
entry init
 call far _compiler_overlay_phase
 cmp ax,2
 jne unavailable
 inc word [cs:nonce]
 jnz .token
 inc word [cs:nonce]
.token:
 push word [cs:nonce]
 push word [cs:_compiler_overlay_expected+16]
 push word [process_psp]
 call far _compiler_lease_init
 add sp,6
 jmp leave
entry info
 call far _compiler_overlay_phase
 cmp ax,2
 jne unavailable
 push word [bp+6]
 call far _compiler_lease_info
 add sp,2
 jmp leave
entry release
 call far _compiler_overlay_phase
 cmp ax,2
 jne unavailable
 xor ax,ax
 push ax
 call far _compiler_lease_info
 add sp,2
 cmp ax,0xffff ; Loaded cookie not initialized: no loan could exist.
 je .safe
 or ax,ax
 jnz unavailable
 mov ax,3
 push ax
 call far _compiler_lease_info
 add sp,2
 cmp ax,1
 jne unavailable
.safe:
 call release_raw
 jmp leave
unavailable:
 mov ax,1
 jmp leave

; All shared-runtime fields are explicitly far, in CONFIG's segment.
config_segment:
 mov ax,seg _line_overlay_state
 mov es,ax
 ret
start:
 call config_segment
 cmp word [es:phase],0
 jne .bad
 cmp word [es:busy],0
 jne .bad
 cmp word [es:fatal],0
 jne .bad
 cmp word [cs:_compiler_overlay_expected],0x434b
 jne .invalid
 cmp word [cs:_compiler_overlay_expected+2],1
 jne .invalid
 mov si,_compiler_overlay_expected+4
 mov di,compiler_overlay_active_expected
 mov cx,6
.copy:
 mov ax,[cs:si]
 mov [es:di],ax
 add si,2
 add di,2
 loop .copy
 cmp word [es:compiler_overlay_active_expected],256
 jb .invalid
 cmp word [es:compiler_overlay_active_expected],8192
 ja .invalid
 cmp word [es:compiler_overlay_active_expected+2],512
 ja .invalid
 mov word [es:compiler_overlay_owner_kind],4
 mov word [es:phase],1
 mov word [es:handle],0xffff
 xor ax,ax
 mov [es:stage],ax
 mov [es:at],ax
 mov [es:fix],ax
 mov [es:busy],ax
 mov [es:dirty],ax
 mov word [es:crc],0xffff
 mov word [es:crc+2],0xffff
 call far compiler_overlay_open
 jc .io
 push ax
 call config_segment
 pop ax
 mov [es:handle],ax
 xor ax,ax
 ret
.io:
 call far compiler_overlay_close
 call config_segment
 mov word [es:phase],3
.invalid:mov ax,4
 ret
.bad:mov ax,1
 ret
global _compiler_overlay_phase
_compiler_overlay_phase:
 push es
 call config_segment
 mov ax,0xffff
 cmp word [es:compiler_overlay_owner_kind],4
 jne .done
 mov ax,[es:phase]
.done:
 pop es
 retf
release_raw:
 call config_segment
 cmp word [es:compiler_overlay_owner_kind],4
 jne .bad
 cmp word [es:busy],0
 jne .bad
 call far compiler_overlay_close
 call config_segment
 cmp word [es:fatal],0
 jne .bad
 mov word [es:phase],0
 xor ax,ax
 ret
.bad:mov ax,1
 ret
