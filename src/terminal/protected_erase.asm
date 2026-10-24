; Checked caller-cleaned ABI for the exact overlay13 protected erase helper.
; Native EL2 temporarily homes only the column. Project its logical offset
; during the helper/repair, preserving the selected pane and all cursor caches.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_abort
extern protected_erase_checked_far
global erase_complex_protected,protected_erase_abort_far
erase_complex_protected:
 push bp
 mov bp,sp
 push word [bp+4]
 call far protected_erase_checked_far
 pop bp
 ret
protected_erase_abort_far:
 mov ax,0xd05f
 jmp terminal_abort

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern protected_erase_native,attribute_plane_admit,attribute_repair_native
extern screen_cursor_wrap,screen_attribute_checks,screen_cursor_row,screen_cursor_column
extern csi_last_row,screen_attribute_row_bytes,screen_attribute_offset
extern erase_attribute_values_base,erase_attribute_values
extern ansi_command,ansi_parameter_count,ansi_parameters
global protected_erase_checked_far,protected_erase_repair,protected_erase_checked_end
protected_erase_checked_far:
 push bp
 mov bp,sp
 sub sp,2
 push si
 push di
 push es
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .invalid
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .invalid
 cmp word [bp+6],1
 ja .invalid
 cmp word [screen_cursor_wrap],1
 jne .invalid
 cmp word [screen_attribute_checks],1
 jne .invalid
 call attribute_plane_admit
 jc .invalid
 cmp word [erase_attribute_values_base],erase_attribute_values
 jne .invalid
 mov ax,[screen_cursor_row]
 cmp ax,[csi_last_row]
 ja .invalid
 mov bx,[screen_cursor_column]
 cmp bx,[screen_attribute_row_bytes]
 jae .invalid
 mul word [screen_attribute_row_bytes]
 add ax,bx
 mov dx,[screen_attribute_offset]
 mov [bp-2],dx
 cmp ax,dx
 je .ready
 ; Only the recovered EL2 dispatcher's temporary column home is admitted.
 or bx,bx
 jnz .invalid
 cmp word [ansi_command],'K'
 jne .invalid
 cmp word [ansi_parameter_count],0
 je .invalid
 cmp word [ansi_parameters],2
 jne .invalid
 cmp dx,ax
 jb .invalid
 mov cx,ax
 add cx,[screen_attribute_row_bytes]
 cmp dx,cx
 jae .invalid
.ready:
 mov [screen_attribute_offset],ax
 push word [bp+6]
 call protected_erase_native
 add sp,2
 mov ax,[bp-2]
 mov [screen_attribute_offset],ax
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf 2
.invalid:
 call far protected_erase_abort_far
protected_erase_repair:
 ; Entry already bounded both planes. Native EL2 can be temporarily outside
 ; the visible pane; the native descriptor handles hidden/visible cells and
 ; needs no pane transition or global video-cursor update.
 push bp
 mov bp,sp
 push word [bp+4]
 call attribute_repair_native
 pop bp
 ret 2
protected_erase_checked_end:
