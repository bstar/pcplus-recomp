; Maintained logical-row ICH/DCH owner. Capture the visible80 cells, move
; bounded words in the owned132-column shadow, then repaint the same pane.
; No allocation, pane transition, UART polling or cursor mutation occurs here.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attribute_geometry_admit_far
extern screen_cursor_wrap,screen_attribute_checks,screen_cursor_row,screen_cursor_column
extern screen_attribute_row_bytes,screen_line_flags,screen_viewport_offset
extern erase_shadow_offset,erase_shadow_segment,attributes_normal_value
extern ansi_parameters,csi_wrap_pending
global character_wide_edit_far,character_wide_end,character_wide_insert_copy,character_wide_delete_copy
; DI0 insert/1 delete. The parser owns repetition; perform one admitted unit.
character_wide_edit_far:
 push bp
 mov bp,sp
 sub sp,14
 push si
 push di
 push es
 mov [bp-14],di
 mov ax,[screen_cursor_wrap]
 or ax,[screen_attribute_checks]
 jnz .refuse
 call far attribute_geometry_admit_far
 jc .refuse
 mov bx,[screen_cursor_row]
 mov dx,1
 test byte [screen_line_flags+bx],0x40
 jz .unit
 mov dx,2
 test byte [screen_cursor_column],1
 jnz .refuse
.unit:
 mov [bp-6],dx
 mov ax,132
 sub ax,[screen_cursor_column]
 cmp ax,dx
 jb .refuse
 mov cx,ax
 cmp dx,2
 jne .count
 shr cx,1
.count:
 mov ax,[ansi_parameters]
 cmp ax,1
 jge .positive
 mov ax,1
.positive:
 cmp ax,cx
 jbe .clipped
 mov ax,cx
.clipped:
 mov [ansi_parameters],ax
 mov ax,bx
 mov cx,160
 mul cx
 mov [bp-10],ax
 mov ax,bx
 mov cx,264
 mul cx
 add ax,[erase_shadow_offset]
 mov [bp-2],ax
 mov dx,[screen_cursor_column]
 shl dx,1
 add dx,ax
 mov [bp-4],dx
 mov ax,[screen_viewport_offset]
 shl ax,1
 mov [bp-12],ax
 mov di,[bp-2]
 add di,ax
 mov es,[erase_shadow_segment]
 mov si,[bp-10]
 push ds
 mov ax,0xb800
 mov ds,ax
 mov cx,80
 cld
 rep movsw
 pop ds
 mov di,[bp-4]
 mov ax,[es:di]
 cmp word [bp-14],0
 je .fill
 mov ah,[attributes_normal_value]
.fill:
 mov al,32
 mov [bp-8],ax
 mov cx,132
 sub cx,[screen_cursor_column]
 sub cx,[bp-6]
 mov si,di
 mov ax,[bp-6]
 shl ax,1
 cmp word [bp-14],0
 jne .delete
 shl cx,1
 add si,cx
 sub si,2
 mov di,si
 add di,ax
 shr cx,1
 push ds
 push es
 pop ds
 std
.insert_copy:
 rep movsw
 cld
 pop ds
 mov di,[bp-4]
 jmp .blank
.delete:
 add si,ax
 push ds
 push es
 pop ds
.delete_copy:
 rep movsw
 pop ds
 mov di,[bp-2]
 add di,264
 sub di,ax
.blank:
 mov ax,[bp-8]
 mov cx,[bp-6]
 rep stosw
 mov si,[bp-2]
 add si,[bp-12]
 mov di,[bp-10]
 push ds
 push es
 pop ds
 mov ax,0xb800
 mov es,ax
 mov cx,80
 rep movsw
 pop ds
 mov word [csi_wrap_pending],0
 jmp .done
.refuse:
 mov word [ansi_parameters],1
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
character_wide_end:
character_wide_insert_copy equ character_wide_edit_far.insert_copy
character_wide_delete_copy equ character_wide_edit_far.delete_copy
