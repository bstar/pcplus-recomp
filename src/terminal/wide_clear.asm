; Maintained bounded132-column clear for overlapping80-column panes. The
; original rectangle assumes disjoint panes and can underflow a hidden fill
; count for a range ending inside columns52..79. Counted scrolling is separate.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attribute_plane_admit,repair_abort_far
extern screen_attribute_row_bytes,screen_viewport_offset,csi_last_row
extern erase_shadow_segment,erase_shadow_offset,erase_lineflags_enabled,screen_line_flags
global terminal_wide_clear_far,terminal_wide_clear_end
; FAR stack attr,bottom/right,top/left,count0. Preserve native RET8 ABI.
terminal_wide_clear_far:
 push bp
 mov bp,sp
 sub sp,12
 push bx
 push si
 push di
 push es
 mov ax,ds
 mov dx,ss
 cmp ax,dx
 jne .bad
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .bad
 cmp word [bp+12],0
 jne .bad
 cmp word [screen_attribute_row_bytes],132
 jne .bad
 call attribute_plane_admit
 jc .bad
 xor ax,ax
 mov al,[bp+10]
 mov [bp-2],ax
 xor dx,dx
 mov dl,[bp+8]
 mov [bp-4],dx
 cmp ax,dx
 ja .bad
 cmp dx,132
 jae .bad
 xor ax,ax
 mov al,[bp+11]
 mov [bp-6],ax
 xor dx,dx
 mov dl,[bp+9]
 mov [bp-8],dx
 cmp ax,dx
 ja .bad
 cmp dx,[csi_last_row]
 ja .bad
 mov al,[bp+6]
 mov ah,al
 mov al,32
 mov [bp-10],ax
 mov ax,[bp-6]
 mov [bp-12],ax
 cmp word [erase_lineflags_enabled],0
 je .row
 cmp ax,[bp-8]
 je .row
 mov bx,ax
.flags:
 mov byte [screen_line_flags+bx],0
 inc bx
 cmp bx,[bp-8]
 jbe .flags
.row:
 mov ax,[bp-12]
 mov cx,264
 mul cx
 add ax,[erase_shadow_offset]
 mov di,[bp-2]
 shl di,1
 add di,ax
 mov cx,[bp-4]
 sub cx,[bp-2]
 inc cx
 mov es,[erase_shadow_segment]
 mov ax,[bp-10]
 cld
 rep stosw
 ; Paint only the intersection with the unchanged visible pane.
 mov si,[bp-2]
 mov bx,[screen_viewport_offset]
 cmp si,bx
 jae .left_ready
 mov si,bx
.left_ready:
 mov dx,bx
 add dx,79
 cmp dx,[bp-4]
 jbe .right_ready
 mov dx,[bp-4]
.right_ready:
 cmp si,dx
 ja .next
 mov cx,dx
 sub cx,si
 inc cx
 sub si,bx
 shl si,1
 mov ax,[bp-12]
 mov bx,160
 mul bx
 mov di,ax
 add di,si
 mov ax,0xb800
 mov es,ax
 mov ax,[bp-10]
 rep stosw
.next:
 inc word [bp-12]
 mov ax,[bp-12]
 cmp ax,[bp-8]
 jbe .row
 pop es
 pop di
 pop si
 pop bx
 mov sp,bp
 pop bp
 retf 8
.bad:
 jmp far repair_abort_far
terminal_wide_clear_end:
