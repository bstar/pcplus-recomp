; Diagnostic only; all code is banked, with no resident helper bytes.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public class=FARCODE use16
global _rows_probe_write
; Far cdecl(name near,buffer near,count); DS=SS. Exclusive create, one close.
_rows_probe_write:
 push bp
 mov bp,sp
 sub sp,2
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov word [bp-2],1
 mov dx,[bp+6]
 xor cx,cx
 mov ax,0x5b00
 int 0x21
 jc .done
 mov bx,ax
 mov dx,[bp+8]
 mov cx,[bp+10]
 mov ah,0x40
 int 0x21
 jc .close
 cmp ax,[bp+10]
 jne .close
 mov word [bp-2],0
.close:
 mov ah,0x3e
 int 0x21
 jnc .done
 mov word [bp-2],1
.done:
 mov ax,[bp-2]
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf
%ifdef TERMINAL_ROW_GEOMETRY_PROBE
global _rows_probe_far
; Far cdecl(name near,buffer far,count). Caller has returned from transaction;
; captured video/shadow IO is diagnostic work, not part of its critical owner.
_rows_probe_far:
 push bp
 mov bp,sp
 sub sp,2
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov word [bp-2],1
 mov dx,[bp+6]
 xor cx,cx
 mov ax,0x5b00
 int 0x21
 jc .done
 mov bx,ax
 mov dx,[bp+8]
 mov ds,[bp+10]
 mov cx,[bp+12]
 mov ah,0x40
 int 0x21
 jc .close
 cmp ax,[bp+12]
 jne .close
 mov word [bp-2],0
.close:
 mov ah,0x3e
 int 0x21
 jnc .done
 mov word [bp-2],1
.done:
 mov ax,[bp-2]
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 retf
%endif

%ifdef TERMINAL_LARGE_VIEW_FRAMES
%ifdef TERMINAL_ROW_GEOMETRY_PROBE
SEGMENT CONFIG_CODE public class=FARCODE use16
extern terminal_redisplay_key_far
global _rows_view_key
_rows_view_key:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,[bp+6]
 call far terminal_redisplay_key_far
 mov ax,0
 adc ax,0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endif

%endif

%ifdef TERMINAL_PROGRAM_DISPLAY
%ifdef TERMINAL_ROW_GEOMETRY_PROBE
SEGMENT _TEXT public class=CODE use16
extern terminal_program_start,terminal_program_poll
extern terminal_program_pending,terminal_program_active,terminal_program_status,terminal_quit
rows_program_run_resident:
 call terminal_program_start
 or ax,ax
 jnz .done
.poll:
 call terminal_program_poll
 cmp word [terminal_quit],0
 jne .status
 mov ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 jnz .poll
.status:
 mov ax,[terminal_program_status]
.done:
 retf
SEGMENT CONFIG_CODE public class=FARCODE use16
global _rows_program_run
_rows_program_run:
 push bp
 mov bp,sp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov ax,[bp+6]
 call far rows_program_run_resident
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endif
%endif

%ifdef TERMINAL_PROFILE_DISPLAY_PROBE
SEGMENT _TEXT public class=CODE use16
extern terminal_setup_start
rows_setup_run_resident:
 call terminal_setup_start
 or ax,ax
 jnz .done
.poll:
 call terminal_program_poll
 cmp word [terminal_quit],0
 jne .status
 mov ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 jnz .poll
.status:
 mov ax,[terminal_program_status]
.done:
 retf
SEGMENT CONFIG_CODE public class=FARCODE use16
global _rows_setup_run
_rows_setup_run:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call far rows_setup_run_resident
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endif

%ifdef TERMINAL_XLT_DISPLAY_PROBE
SEGMENT _TEXT public class=CODE use16
extern terminal_translation_edit_start
rows_xlt_run_resident:
 call terminal_translation_edit_start
 or ax,ax
 jnz .done
.poll:
 call terminal_program_poll
 cmp word [terminal_quit],0
 jne .status
 mov ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 jnz .poll
.status:
 mov ax,[terminal_program_status]
.done:
 retf
SEGMENT CONFIG_CODE public class=FARCODE use16
global _rows_xlt_run
_rows_xlt_run:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call far rows_xlt_run_resident
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 retf
%endif
