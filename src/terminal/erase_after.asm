; Normalize the recovered EL2 temporary column home for every wrapped erase
; path, including monochrome/unprotected metadata erasure and tail repair.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_erase_after_far,terminal_erase_after_native
global csi_service_d8b6,terminal_erase_after_native_far
csi_service_d8b6:
 push bp
 mov bp,sp
 push word [bp+4]
 call far terminal_erase_after_far
 pop bp
 ret 2
terminal_erase_after_native_far:
 push bp
 mov bp,sp
 push word [bp+6]
 call terminal_erase_after_native
 pop bp
 retf 2
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern screen_cursor_wrap,attribute_plane_admit,protected_erase_abort_far
extern screen_cursor_row,screen_cursor_column,csi_last_row,screen_attribute_row_bytes
extern screen_attribute_offset,erase_attribute_values_base,erase_attribute_values
extern ansi_command,ansi_parameter_count,ansi_parameters
global terminal_erase_after_far,erase_after_projection_active
erase_after_projection_active: dw 0
terminal_erase_after_far:
 push bp
 mov bp,sp
 sub sp,2
 push si
 push di
 push es
 cmp word [screen_cursor_wrap],0
 je .plain
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 cmp word [cs:erase_after_projection_active],0
 jne .bad
 cmp word [bp+6],1
 ja .bad
 call attribute_plane_admit
 jc .bad
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .bad
 mov ax,[screen_cursor_row]
 cmp ax,[csi_last_row]
 ja .bad
 mov bx,[screen_cursor_column]
 cmp bx,[screen_attribute_row_bytes]
 jae .bad
 mul word [screen_attribute_row_bytes]
 add ax,bx
 mov dx,[screen_attribute_offset]
 mov [bp-2],dx
 cmp ax,dx
 je .project
 or bx,bx
 jnz .bad
 cmp word [ansi_command],'K'
 jne .bad
 cmp word [ansi_parameter_count],0
 je .bad
 cmp word [ansi_parameters],2
 jne .bad
 cmp dx,ax
 jb .bad
 mov cx,ax
 add cx,[screen_attribute_row_bytes]
 cmp dx,cx
 jae .bad
.project:
 mov [screen_attribute_offset],ax
 mov word [cs:erase_after_projection_active],1
 push word [bp+6]
 call far terminal_erase_after_native_far
 mov word [cs:erase_after_projection_active],0
 mov ax,[bp-2]
 mov [screen_attribute_offset],ax
 jmp .done
.plain:
 push word [bp+6]
 call far terminal_erase_after_native_far
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf 2
.bad:
 jmp far protected_erase_abort_far
