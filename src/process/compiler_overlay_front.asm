; Retained parent frontend; live compiler RPC is an explicit opt-in extension.
BITS 16
CPU 8086
; Interpreter result namespace, matching src/aspect/runtime.h (not lease codes).
%define ASPECT_RUN_IO 5
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
%ifdef TERMINAL_CONNECTION_ARENA
; PCCONN (shared owner kind5) reuses start/poll/phase/release below. Fields
; follow the compiler descriptor: 'CN', version, the six loader words, the
; retained paragraph cut (PSP-relative extent end), allocated image bytes
; (file payload plus BSS/stack) and the module entry offset. All are written
; after linking by standalone/build_terminal.py from the matched parent map.
global _connection_overlay_expected
_connection_overlay_expected: dw 0x4e43,1,0,0,0,0,0,0,0,0,0
%define CONNECTION_EXTENT 16384
; Selected front owner. Every public entry selects its own owner first.
front_kind: dw 4
front_desc: dw _compiler_overlay_expected
%endif
%ifdef TERMINAL_COMPILER_LEASE_BRIDGE
bridge_owner: dw 0
bridge_active: dw 0
extern terminal_program_active,terminal_program_kind,terminal_irq_vector
extern _compiler_lease_begin,_compiler_lease_end,redisplay_snapshot
; First8006 snapshot bytes are compiler-owned while kind4 holds the arena.
; The kernel starts at16384, so this frame remains below the retained cut.
%define screen_meta redisplay_snapshot+8000
%endif
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
%ifdef TERMINAL_CONNECTION_ARENA
 call select_compiler
%endif
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
%ifndef TERMINAL_COMPILER_LEASE_BRIDGE
; Startup diagnostics are a separate build; live admission keeps its own guards.
context:
 call context_common
 or ax,ax
 jz .bad
 cmp byte [hardware_active],0
 jne .bad
 cmp byte [vector_active],0
 jne .bad
 mov ah,0x51
 int 0x21
 cmp bx,[process_psp]
 jne .bad
 mov ax,1
 ret
.bad:xor ax,ax
 ret
%endif
; Retained parent stack/data and MCB are valid even while the later tail is lent.
context_common:
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
 mov ax,[_redisplay_active]
 or ax,[_command_menu_active]
 or ax,[_redisplay_live_ready]
 jnz .bad
 mov bx,[process_psp]
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
%ifdef TERMINAL_CONNECTION_ARENA
 mov si,[cs:front_desc]
 mov ax,[cs:si+16]
%else
 mov ax,[cs:_compiler_overlay_expected+16]
%endif
 cmp ax,[es:3]
 ja .bad
 mov ax,1
 ret
.bad:xor ax,ax
 ret
%ifndef TERMINAL_COMPILER_LEASE_BRIDGE
entry load
 call load_module
 jmp leave
%endif
load_module:
 call start
 cmp ax,1
 je .return
 or ax,ax
 jnz .failed
 mov cx,64
.poll:
 call far _line_port_front_poll
%ifdef TERMINAL_CONNECTION_ARENA
 call front_phase
%else
 call far _compiler_overlay_phase
%endif
 cmp ax,2
 je .ready
 cmp ax,1
 jne .failed
 loop .poll
.failed:
 call release_raw
 mov ax,4
 ret
.ready:
 xor ax,ax
.return:ret
%ifndef TERMINAL_COMPILER_LEASE_BRIDGE
entry init
 call init_module
 jmp leave
%endif
init_module:
 call far _compiler_overlay_phase
 cmp ax,2
 je .ready
 mov ax,1
 ret
.ready:
 inc word [cs:nonce]
 jnz .token
 inc word [cs:nonce]
.token:
 push word [cs:nonce]
 push word [cs:_compiler_overlay_expected+16]
 push word [process_psp]
 call far _compiler_lease_init
 add sp,6
 ret
%ifndef TERMINAL_COMPILER_LEASE_BRIDGE
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
%endif

%ifdef TERMINAL_CONNECTION_ARENA
%ifdef TERMINAL_COMPILER_LEASE_BRIDGE
%error PCCONN entries are startup-only until live connection admission exists
%endif
; Startup-only PCCONN owner (kind5): same parent context, same bounded loader.
%macro connection_entry 1
global _connection_overlay_%1
_connection_overlay_%1:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 call select_connection
 call context
 or ax,ax
 jnz %%valid
 mov ax,2
 jmp leave
%%valid:
%endmacro
select_connection:
 mov word [cs:front_kind],5
 mov word [cs:front_desc],_connection_overlay_expected
 ret
; AX0 ready with BSS/stack zeroed; 1 already owned/busy/fatal; 4 refused or
; failed load, already released (or left fatal by a failed close).
connection_entry load
 call load_module
 or ax,ax
 jnz .done
 call clear_image
 xor ax,ax
.done:jmp leave
; AX0 released; 1 not the ready connection owner.
connection_entry release
 call front_phase
 cmp ax,2
 mov ax,1
 jne .done
 call release_raw
.done:jmp leave
global _connection_overlay_phase,_connection_overlay_arena
_connection_overlay_phase:
 push word [cs:front_kind]
 mov word [cs:front_kind],5
 call front_phase
 pop word [cs:front_kind]
 retf
; While ready: DX=arena segment, AX=allocated image bytes, CX=entry offset.
; Otherwise AX=0. No admission or state change.
_connection_overlay_arena:
 push es
 push word [cs:front_kind]
 mov word [cs:front_kind],5
 call front_phase
 pop word [cs:front_kind]
 cmp ax,2
 mov ax,0
 jne .done
 call arena_segment
 mov ax,[cs:_connection_overlay_expected+18]
 mov cx,[cs:_connection_overlay_expected+20]
.done:
 pop es
 retf
; DX=load base+target from the active descriptor (DS=SS parent stack).
arena_segment:
 call config_segment
 mov dx,ss
 sub dx,[es:compiler_overlay_active_expected+10]
 add dx,[es:compiler_overlay_active_expected+8]
 ret
; The loader stops at the file image; DOS MZ semantics leave BSS undefined, so
; establish zero BSS/stack from payload end to the allocated image end.
clear_image:
 call arena_segment
 mov di,[es:compiler_overlay_active_expected]
 mov cx,[cs:_connection_overlay_expected+18]
 sub cx,di
 mov es,dx
 xor ax,ax
 cld
 rep stosb
 ret
%endif

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
%ifdef TERMINAL_CONNECTION_ARENA
 mov si,[cs:front_desc]
 mov ax,0x434b
 cmp word [cs:front_kind],4
 je .magic
 mov ax,0x4e43
.magic:
 cmp [cs:si],ax
 jne .invalid
 cmp word [cs:si+2],1
 jne .invalid
 add si,4
%else
 cmp word [cs:_compiler_overlay_expected],0x434b
 jne .invalid
 cmp word [cs:_compiler_overlay_expected+2],1
 jne .invalid
 mov si,_compiler_overlay_expected+4
%endif
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
%ifdef TERMINAL_CONNECTION_ARENA
 cmp word [cs:front_kind],4
 jne .connection_bound
%endif
 cmp word [es:compiler_overlay_active_expected],8192
 ja .invalid
%ifdef TERMINAL_CONNECTION_ARENA
.connection_bound:
%endif
 cmp word [es:compiler_overlay_active_expected+2],512
 ja .invalid
%ifdef TERMINAL_CONNECTION_ARENA
 cmp word [cs:front_kind],4
 je .owner
 ; Payload, fixup table and the loader's EOF probe byte must all lie inside
 ; the exclusive extent, and so must the allocated image (BSS and stack).
 mov ax,[es:compiler_overlay_active_expected+2]
 shl ax,1
 add ax,[es:compiler_overlay_active_expected]
 cmp ax,CONNECTION_EXTENT-1
 ja .invalid
 mov si,[cs:front_desc]
 mov ax,[cs:si+18]
 cmp ax,CONNECTION_EXTENT
 ja .invalid
 cmp ax,[es:compiler_overlay_active_expected]
 jb .invalid
 cmp [cs:si+20],ax
 jae .invalid
.owner:
 mov ax,[cs:front_kind]
 mov [es:compiler_overlay_owner_kind],ax
%else
 mov word [es:compiler_overlay_owner_kind],4
%endif
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
%ifdef TERMINAL_CONNECTION_ARENA
; Public phase is always the compiler's, whichever front owner is selected.
_compiler_overlay_phase:
 push word [cs:front_kind]
 mov word [cs:front_kind],4
 call front_phase
 pop word [cs:front_kind]
 retf
; Near: AX=shared phase when the selected owner holds it, else FFFF.
front_phase:
 push es
 call config_segment
 mov ax,[es:compiler_overlay_owner_kind]
 cmp ax,[cs:front_kind]
 mov ax,0xffff
 jne .done
 mov ax,[es:phase]
.done:
 pop es
 ret
select_compiler:
 mov word [cs:front_kind],4
 mov word [cs:front_desc],_compiler_overlay_expected
 ret
%else
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
%endif
release_raw:
 call config_segment
%ifdef TERMINAL_CONNECTION_ARENA
 mov ax,[cs:front_kind]
 cmp [es:compiler_overlay_owner_kind],ax
%else
 cmp word [es:compiler_overlay_owner_kind],4
%endif
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

%ifdef TERMINAL_COMPILER_LEASE_BRIDGE
; Called only after the renderer authenticates client/callback and flow scope.
; Foreground runs DS=SS on retained parent stack, CurrentPDB remains the child.
global _compiler_overlay_bridge,_compiler_overlay_loaned,_compiler_overlay_retire
_compiler_overlay_loaned:
 mov ax,[cs:bridge_active]
 retf
_compiler_overlay_retire:
 ; Renderer revocation is an assembly service, not a C call. Preserve its
 ; incoming register/flag contract even when close has no open descriptor.
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 cmp word [cs:bridge_active],0
 jne fatal_parent
%ifdef TERMINAL_CONNECTION_ARENA
 call select_compiler
%endif
 call release_raw
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
_compiler_overlay_bridge:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
%ifdef TERMINAL_CONNECTION_ARENA
 call select_compiler
%endif
 call context_common
 or ax,ax
 jz .identity
 cmp word [terminal_program_active],1
 jne .identity
 cmp word [terminal_program_kind],4
 jne .identity
 mov ah,0x51
 int 0x21
 cmp bx,[bp+8]
 jne .identity
 cmp bx,[process_psp]
 je .identity
 mov es,bx
 mov ax,[process_psp]
 cmp [es:0x16],ax
 jne .identity
 cmp word [es:0],0x20cd
 jne .identity
 dec bx
 mov es,bx
 mov ax,[bp+8]
 cmp [es:1],ax
 jne .identity
 ; vector_active is a parent cleanup marker, not current IRQ ownership.
 mov cx,[es:3]
 add cx,ax
 jc .identity
 mov di,ax
 add di,16
 jc .identity
 mov ax,[terminal_irq_vector]
 mov ah,0x35
 int 0x21
 mov ax,es
 shr bx,1
 shr bx,1
 shr bx,1
 shr bx,1
 add ax,bx
 jc .identity
 cmp ax,di
 jb .identity
 cmp ax,cx
 jae .identity
 cmp word [bp+6],1
 je .end
 cmp word [bp+6],0
 jne .identity
 cmp word [cs:bridge_active],0
 jne .identity
 mov ax,[bp+8]
 mov [cs:bridge_owner],ax
 call load_module
 or ax,ax
 jnz .intact_error
 ; Init alone is scoped to parent PSP; no file operation crosses that scope.
 ; DOS records its entry stack at CurrentPDB:2E, including AH50. Keep the
 ; suspended outer EXEC stack intact until identity is back with the child.
 mov es,[process_psp]
 push word [es:0x2e]
 push word [es:0x30]
 mov bx,[process_psp]
 mov ah,0x50
 int 0x21
 call init_module
 push ax
 mov bx,[cs:bridge_owner]
 mov ah,0x50
 int 0x21
 mov es,[process_psp]
 pop ax
 pop word [es:0x30]
 pop word [es:0x2e]
 push ax
 mov ah,0x51
 int 0x21
 cmp bx,[cs:bridge_owner]
 pop ax
 jne .identity
 or ax,ax
 jnz .begin_failed
 call capture_screen
 or ax,ax
 jnz .screen_failed
 push word [cs:bridge_owner]
 push word [cs:nonce]
 call far _compiler_lease_begin
 add sp,4
 or ax,ax
 jnz .begin_failed
 mov word [cs:bridge_active],1
 xor ax,ax
 jmp leave
.screen_failed:
 call release_raw
 mov ax,0xe003
 jmp leave
.begin_failed:
 call release_raw ; Begin refusal never lent memory; stale temp cleanup may fail.
.intact_error:
 mov ax,0xe000 | ASPECT_RUN_IO
 jmp leave
.end:
 cmp word [cs:bridge_active],1
 jne .intact_state
 mov ax,[bp+8]
 cmp ax,[cs:bridge_owner]
 jne .identity
 push ax
 push word [cs:nonce]
 call far _compiler_lease_end
 add sp,4
 mov si,ax
 mov ax,3
 push ax
 call far _compiler_lease_info
 add sp,2
 cmp ax,1
 jne .identity ; No safe-retirement tag while memory is invalid.
 mov word [cs:bridge_active],0
 ; No video/frame access until the kernel attests valid memory. Compiler and
 ; BIOS recovery output are temporary; restore the exact captured display.
 push si
 call restore_screen
 pop si
 call release_raw
 xor ax,ax
 or si,si
 jz .returned
 mov ax,0xe000 | ASPECT_RUN_IO
.returned:jmp leave
.intact_state:
 mov ax,0xe00a
 jmp leave
.identity:
 mov ax,10
 jmp leave
; No CRT, allocation, callbacks or data borrowing across this video-DS window.
; Only verified mode3/page0/80-column25/28/43/50-row frames are captured.
capture_screen:
 push ds
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x49],3
 jne .bad
 cmp word [es:0x4a],80
 jne .bad
 cmp byte [es:0x62],0
 jne .bad
 xor ax,ax
 mov al,[es:0x84]
 inc ax
 cmp ax,1
 jne .rows
 mov ax,25 ; Older BIOS has no last-row byte.
.rows:
 cmp ax,25
 je .size
 cmp ax,28
 je .size
 cmp ax,43
 je .size
 cmp ax,50
 jne .bad
.size:
 mov cx,80
 mul cx
 push ax
 mov ah,3
 xor bh,bh
 int 0x10
 mov ax,seg redisplay_snapshot
 mov es,ax
 mov di,screen_meta
 pop ax
 cld
 stosw
 mov ax,cx
 stosw
 mov ax,dx
 stosw
 mov cx,[es:screen_meta]
 mov di,redisplay_snapshot
 mov ax,0xb800
 mov ds,ax
 xor si,si
 rep movsw
 pop ds
 xor ax,ax
 ret
.bad:
 pop ds
 mov ax,3
 ret
restore_screen:
 push ds
 mov ax,seg redisplay_snapshot
 mov ds,ax
 mov cx,[screen_meta]
 push word [screen_meta+4]
 push word [screen_meta+2]
 mov si,redisplay_snapshot
 mov ax,0xb800
 mov es,ax
 xor di,di
 cld
 rep movsw
 pop cx
 mov ah,1
 int 0x10
 pop dx
 xor bh,bh
 mov ah,2
 int 0x10
 pop ds
 ret
; Unexpected child termination during an invalid loan must never repaint/free
; through the missing tail. This deliberate fail-stop is not ordinary recovery.
fatal_parent:
 mov si,fatal_text
.next:
 mov al,[cs:si]
 inc si
 or al,al
 jz .halt
 mov ah,0x0e
 xor bx,bx
 int 0x10
 jmp .next
.halt:
 sti
 hlt
 jmp .halt
fatal_text: db 13,10,'Parent memory restore incomplete. Reboot required.',13,10,0
%endif
