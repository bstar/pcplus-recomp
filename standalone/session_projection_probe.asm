; Diagnostic-only source caller of the production far projection API.
BITS 16
CPU 8086
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
extern _terminal_session_project
%ifdef TERMINAL_SESSION_BASELINE
extern _terminal_session_project_bound,terminal_baseline_storage
%endif
%ifdef TERMINAL_SESSION_CONTROLS
extern _terminal_mouse_offer_far,_terminal_mouse_commit_far,_terminal_sound_enabled
%endif
global terminal_session_projection_probe_far
terminal_session_projection_probe_far:
 push bp
 mov bp,sp
 sub sp,2530
 push ds
 pop es
 lea di,[bp-2528]
 mov ax,0x5858
 mov cx,632
 cld
 rep stosw
%ifdef TERMINAL_SESSION_BASELINE
 ; Remove the original startup spelling before asking for the retained image.
 ; This diagnostic runs only against its private TEST.PRM fixture.
 push ds
 push cs
 pop ds
 mov ax,ds
 mov es,ax
 mov dx,startup_name
 mov di,away_name
 mov ax,0x5600
 int 0x21
 pop ds
 jc .failed
%ifdef TERMINAL_SESSION_CONTROLS
 ; Controlled diagnostic mutation after startup acceptance. Use the owner's
 ; normal offer/commit APIs; no native mouse driver has been acquired here.
 push ds
 pop es
 lea di,[bp-1264]
 xor ax,ax
 mov cx,632
 cld
 rep stosw
 mov word [bp-1264+0x4e4],999
 mov word [bp-1264+0x4e6],1
 mov ax,1264
 push ax
 lea ax,[bp-1264]
 push ax
 call far _terminal_mouse_offer_far
 add sp,4
 cmp ax,16384
 jne .failed
 call far _terminal_mouse_commit_far
 or ax,ax
 jnz .failed
 xor word [_terminal_sound_enabled],1
%endif
 lea ax,[bp-2528]
 push ax
 call far _terminal_session_project_bound
 add sp,2
%else
 push ds
 push cs
 pop ds
 mov dx,baseline_name
 mov ax,0x3d00
 int 0x21
 pop ds
 jc .failed
 mov bx,ax
 lea dx,[bp-1264]
 mov cx,1264
 mov ah,0x3f
 int 0x21
 jc .failed
 cmp ax,1264
 jne .failed
 lea dx,[bp-2530]
 mov cx,1
 mov ah,0x3f
 int 0x21
 jc .failed
 or ax,ax
 jnz .failed
 mov ah,0x3e
 int 0x21
 jc .failed
 lea ax,[bp-2528]
 push ax
 lea ax,[bp-1264]
 push ax
 call far _terminal_session_project
 add sp,4
%endif
 mov [bp-2530],ax
 mov si,output_name
 lea dx,[bp-2528]
 mov cx,1264
 call .write
 jc .failed
%ifdef TERMINAL_SESSION_BASELINE
 push ds
 push cs
 pop ds
 mov si,state_name
 mov dx,terminal_baseline_storage
 mov cx,1272
 call .write
 pop ds
 jc .failed
%endif
 mov si,status_name
 lea dx,[bp-2530]
 mov cx,2
 call .write
 jc .failed
 xor ax,ax
 jmp .done
.failed:
 mov ax,1
.done:
 mov sp,bp
 pop bp
 retf
; CS:SI file, DS:DX near bytes,CX count. CF reports any open/write/close error.
.write:
 push cx
 push dx
 push ds
 push cs
 pop ds
 mov dx,si
 xor cx,cx
 mov ah,0x3c
 int 0x21
 pop ds
 pop dx
 pop cx
 jc .write_done
 mov bx,ax
 push cx
 mov ah,0x40
 int 0x21
 pop cx
 jc .write_done
 cmp ax,cx
 jne .short
 mov ah,0x3e
 int 0x21
.write_done:
 ret
.short:
 stc
 ret
baseline_name: db 'PBASE.BIN',0
output_name: db 'POUT.BIN',0
status_name: db 'PSTAT.BIN',0
%ifdef TERMINAL_SESSION_BASELINE
startup_name: db 'TEST.PRM',0
away_name: db 'AWAY.PRM',0
state_name: db 'BSTATE.BIN',0
%endif
