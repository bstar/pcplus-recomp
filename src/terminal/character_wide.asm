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
extern ansi_parameters,csi_wrap_pending,screen_attribute_offset
extern screen_attributes_base,erase_attribute_values_base,attribute_repair_checked_far
global character_wide_edit_far,character_wide_end,character_wide_insert_copy,character_wide_delete_copy
; DI0 insert/1 delete. The parser owns repetition; perform one admitted unit.
global character_wide_prepare_far
character_wide_prepare_far:
 push bp
 mov bp,sp
 sub sp,20
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
 call character_wide_edit_far.prepare
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 mov sp,bp
 pop bp
 retf
character_wide_edit_far:
 push bp
 mov bp,sp
 sub sp,20
 push si
 push di
 push es
 call .prepare
 jc .done
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
 mov cx,[bp-16]
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
 mov di,[bp-16]
 shl di,1
 add di,[bp-2]
 sub di,ax
.blank:
 cmp word [screen_cursor_wrap],0
 je .same_fill
 cmp word [screen_attribute_checks],0
 jne .protected_fill
 push di
 call .metadata
 pop di
 jmp .value_fill
.protected_fill:
 cmp word [bp-14],0
 je .same_fill
.value_fill:
 mov si,di
 sub si,[bp-2]
 shr si,1
 add si,[bp-20]
 sub si,[screen_cursor_column]
 add si,[erase_attribute_values_base]
 mov cx,[bp-6]
.value_cell:
 mov ah,[si]
 mov al,32
 stosw
 inc si
 loop .value_cell
 jmp .paint
.same_fill:
 mov ax,[bp-8]
 mov cx,[bp-6]
 rep stosw
.paint:
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
 cmp word [bp-18],0
 je .complete
 mov ax,2
 push ax
 call far attribute_repair_checked_far
.complete:
 mov word [csi_wrap_pending],0
 jmp .done
.done:
 pop es
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
.prepare:
 mov [bp-14],di
 call far attribute_geometry_admit_far
 jc .prepare_bad
 mov ax,[screen_attribute_offset]
 mov [bp-20],ax
 mov word [bp-18],0
 mov word [bp-16],132
 cmp word [screen_attribute_checks],0
 je .field_ready
 mov si,[screen_attributes_base]
 add si,ax
 mov dx,[screen_cursor_column]
 mov cx,132
 sub cx,dx
.field_scan:
 test byte [si],0x81
 jnz .boundary
 inc si
 inc dx
 loop .field_scan
 jmp .field_ready
.boundary:
 mov [bp-16],dx
.field_ready:
 mov bx,[screen_cursor_row]
 mov dx,1
 test byte [screen_line_flags+bx],0x40
 jz .unit
 mov dx,2
 test byte [screen_cursor_column],1
 jnz .prepare_bad
.unit:
 mov [bp-6],dx
 mov ax,[bp-16]
 sub ax,[screen_cursor_column]
 cmp ax,dx
 jb .prepare_bad
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
 clc
 ret
.prepare_bad:
 mov word [ansi_parameters],1
 stc
 ret

; Move only this field/row's metadata. Keep the vacated values and marker
; bits, clearing the protection bit in each vacated cell. Double-width moves
; keep both metadata cells paired with the two video cells.
.metadata:
 push es
 push ds
 pop es
 mov si,[screen_attributes_base]
 add si,[bp-20]
 cmp word [bp-14],0
 je .planes
 mov cx,[bp-6]
.marker_scan:
 test byte [si],0x80
 jz .marker_next
 mov word [bp-18],1
.marker_next:
 inc si
 loop .marker_scan
.planes:
 mov ax,[screen_attributes_base]
 call .plane_shift
 mov ax,[erase_attribute_values_base]
 call .plane_shift
 mov bx,[bp-20]
 cmp word [bp-14],0
 je .vacated
 add bx,[bp-16]
 sub bx,[screen_cursor_column]
 sub bx,[bp-6]
.vacated:
 add bx,[screen_attributes_base]
 mov cx,[bp-6]
.clear_protection:
 and byte [bx],0xfe
 inc bx
 loop .clear_protection
 pop es
 ret
.plane_shift:
 mov si,ax
 add si,[bp-20]
 mov di,si
 mov cx,[bp-16]
 sub cx,[screen_cursor_column]
 sub cx,[bp-6]
 cmp word [bp-14],0
 jne .plane_delete
 add si,cx
 dec si
 mov di,si
 add di,[bp-6]
 std
 rep movsb
 cld
 ret
.plane_delete:
 add si,[bp-6]
 rep movsb
 ret
character_wide_end:
character_wide_insert_copy equ character_wide_edit_far.insert_copy
character_wide_delete_copy equ character_wide_edit_far.delete_copy
