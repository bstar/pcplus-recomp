; Maintained qualified-EXE P_WAIT compiler call. Source/path admission, stdio
; redirection, IRQ pause and divide/vector scope remain with source_compile.c.
; No PATH/BAT dispatch or parent heap resize; use the caller-packed effective
; environment segment and inherit DOS handles.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _aspect_compiler_exec,_aspect_compiler_errno
extern __set_errno_dos_
_aspect_compiler_errno:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 pop bp
 jmp __set_errno_dos_
_aspect_compiler_exec:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 sub sp,216 ;128-byte tail,14-byte parameter block,two37-byte FCBs.
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .context_error
 pushf
 pop ax
 test ax,0x0200
 jz .invalid
 cmp word [cs:busy],0
 jne .invalid
 cmp word [bp+4],0
 je .invalid
 mov si,[bp+6]
 or si,si
 jz .invalid
 xor cx,cx
.length:
 lodsb
 or al,al
 jz .tail
 inc cx
 cmp cx,125
 jbe .length
 mov ax,10 ;DOS argument/environment size -> CRT E2BIG.
 jmp .error
.tail:
 push ds
 pop es
 lea di,[bp-224]
 mov ax,cx
 inc ax
 stosb
 mov al,' '
 stosb
 mov si,[bp+6]
 rep movsb
 mov al,13
 stosb
 lea di,[bp-82]
 xor ax,ax
 mov cx,37
 rep stosw
 lea di,[bp-96]
 mov ax,[bp+8]
 mov [di],ax
 lea ax,[bp-224]
 mov [di+2],ax
 mov [di+4],ds
 lea ax,[bp-82]
 mov [di+6],ax
 mov [di+8],ds
 lea ax,[bp-45]
 mov [di+10],ax
 mov [di+12],ds
 lea si,[bp-223]
 lea di,[bp-82]
 mov ax,0x2901
 int 0x21
 lea di,[bp-45]
 mov ax,0x2901
 int 0x21
 lea bx,[bp-96]
 mov dx,[bp+4]
 mov [cs:saved_ds],ds
 mov [cs:saved_ss],ss
 mov [cs:saved_sp],sp
 mov [cs:saved_bp],bp
 push ds
 pop es
 mov word [cs:busy],1
 mov ax,0x4b00
 int 0x21
 ; DOS/child may leave DS and stack context changed. Use CS before restoring.
 mov [cs:exec_ax],ax
 mov byte [cs:exec_failed],0
 jnc .restore
 mov byte [cs:exec_failed],1
.restore:
 cli
 mov ss,[cs:saved_ss]
 mov sp,[cs:saved_sp]
 mov ds,[cs:saved_ds]
 mov bp,[cs:saved_bp]
 sti
 mov word [cs:busy],0
 cmp byte [cs:exec_failed],0
 jne .dos_error
 mov ah,0x4d
 int 0x21
 jmp .done
.dos_error:
 mov ax,[cs:exec_ax]
 jmp .error
.invalid:
 mov ax,1
.error:
 ; Watcom's existing near register-call mapper preserves DOS/errno semantics.
 call __set_errno_dos_
.context_error:
 mov ax,0xffff ;A foreign DS must never address the CRT errno cell.
.done:
 lea sp,[bp-8]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
busy: dw 0
saved_ds: dw 0
saved_ss: dw 0
saved_sp: dw 0
saved_bp: dw 0
exec_ax: dw 0
exec_failed: db 0
