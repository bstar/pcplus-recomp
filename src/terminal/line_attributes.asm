; Maintained NETWORK line metadata owner. Exact native line helpers remain
; resident for video and ORIGINAL policy; no fixed23-row plane copies run here.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern screen_cursor_wrap,attributes_normal_value,screen_cursor_row
extern screen_cursor_column,screen_last_row,screen_attribute_offset
extern screen_attributes_base,erase_attribute_values_base,erase_cell_count
extern line_native_insert_far,line_native_delete_far
extern repair_previous_attribute,attribute_repair_native,attribute_repair_admit
extern repair_abort_far
global terminal_line_insert_far,terminal_line_delete_far
terminal_line_insert_far:
 xor ax,ax
 jmp line_edit
terminal_line_delete_far:
 mov ax,1
line_edit:
 push bp
 mov bp,sp
 sub sp,6
 push si
 push di
 mov [bp-2],ax ;0 insert,1 delete
 cmp word [screen_cursor_wrap],0
 je .video_only
 call attribute_repair_admit
 jnc .admitted
 call far repair_abort_far
.admitted:
 ; Fill insertion with the previous attribute at this row's start; deletion
 ; uses the previous attribute at the region's end, not the whole plane's end.
 mov ax,[screen_attribute_offset]
 sub ax,[screen_cursor_column]
 cmp word [bp-2],0
 je .previous
 mov ax,[screen_last_row]
 inc ax
 mov dx,80
 mul dx
.previous:
 push ax
 call repair_previous_attribute
 xor ah,ah
 mov [bp-4],ax
 mov word [bp-6],0
 cmp word [bp-2],0
 je .native_video
 ; A deleted field boundary requires repaint of its surviving region.
 mov si,[screen_attribute_offset]
 sub si,[screen_cursor_column]
 add si,[screen_attributes_base]
 mov cx,80
.scan:
 test byte [si],0x80
 jz .next
 mov word [bp-6],1
.next:
 inc si
 loop .scan
.native_video:
 push word [attributes_normal_value]
 push word [screen_cursor_wrap]
 mov ax,[bp-4]
 mov [attributes_normal_value],ax
 mov word [screen_cursor_wrap],0
 call .video
 pop word [screen_cursor_wrap]
 pop word [attributes_normal_value]
 ; The native cursor home has supplied the admitted row-start offset.
 push ds
 pop es
 mov si,[screen_attributes_base]
 call .shift
 mov si,[erase_attribute_values_base]
 call .shift
 mov di,[screen_attribute_offset]
 cmp word [bp-2],0
 je .fill
 mov ax,[screen_last_row]
 mov dx,80
 mul dx
 mov di,ax
.fill:
 mov si,di
 add di,[screen_attributes_base]
 xor ax,ax
 mov cx,80
 rep stosb
 mov di,si
 add di,[erase_attribute_values_base]
 mov ax,[bp-4]
 mov cx,80
 rep stosb
 cmp word [bp-2],0
 je .done
 cmp word [bp-6],0
 je .done
 mov ax,[screen_cursor_row]
 cmp ax,[screen_last_row]
 je .done
 ; The exact native mode2 repair stops at the end of the active region.
 ; Admission checked the real backing before any mutation. Keep the logical
 ; whole-plane count unchanged outside this synchronous native call.
 push word [erase_cell_count]
 mov ax,[screen_last_row]
 inc ax
 mov dx,80
 mul dx
 mov [erase_cell_count],ax
 mov ax,2
 push ax
 call attribute_repair_native
 pop word [erase_cell_count]
 jmp .done
.video_only:
 call .video
.done:
 pop di
 pop si
 mov sp,bp
 pop bp
 retf
.video:
 cmp word [bp-2],0
 jne .delete_video
 call far line_native_insert_far
 ret
.delete_video:
 call far line_native_delete_far
 ret
.shift:
 ; SI names one admitted near plane. Overlap is intentional and directional.
 add si,[screen_attribute_offset]
 mov di,si
 mov ax,[screen_last_row]
 sub ax,[screen_cursor_row]
 mov dx,80
 mul dx
 mov cx,ax
 cmp word [bp-2],0
 jne .forward
 jcxz .shift_done
 add si,cx
 dec si
 mov di,si
 add di,80
 std
 rep movsb
 cld
 ret
.forward:
 add si,80
 rep movsb
.shift_done:
 ret
