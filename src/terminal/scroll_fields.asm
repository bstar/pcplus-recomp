; Bounded live field metadata around the unchanged native rectangle/video code.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_rectangle_native,terminal_scroll_up_native
extern screen_cursor_wrap
global csi_service_2530,scroll_up,scroll_up_bridge_end,terminal_rectangle_native_far
csi_service_2530:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call far terminal_rectangle_far
 pop bp
 ret 8
terminal_rectangle_native_far:
 push bp
 mov bp,sp
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call terminal_rectangle_native
 pop bp
 retf 8
scroll_up:
 cmp word [screen_cursor_wrap],0
 jne .fields
 jmp terminal_scroll_up_native
.fields:
 call far terminal_scroll_up_far
 ret
scroll_up_bridge_end:

SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
extern attribute_repair_plane_admit,repair_abort_far
extern repair_previous_attribute,attribute_repair_native,terminal_region_metadata_move
extern screen_cursor_row,screen_cursor_column,screen_attribute_offset
extern screen_first_row,screen_last_row,screen_last_column,csi_last_row
extern screen_attribute_row_bytes,screen_attributes_base,erase_attribute_values_base,erase_cell_count
extern scroll_skip_attribute_scan,csi_wrap_pending,terminal_wide_clear_far
global terminal_rectangle_far,terminal_scroll_up_far,scroll_region_repair,terminal_rectangle_end
terminal_scroll_up_far:
 push bp
 push si
 push di
 push es
 call attribute_repair_plane_admit
 jc .invalid
 mov ax,[screen_last_row]
 inc ax
 mul word [screen_attribute_row_bytes]
 push ax
 call repair_previous_attribute
 xor ah,ah
 mov si,ax
 mov ax,1
 push ax
 mov ah,[screen_first_row]
 xor al,al
 push ax
 mov ah,[screen_last_row]
 mov al,[screen_last_column]
 push ax
 push si
 call far terminal_rectangle_far
 mov word [csi_wrap_pending],0
 pop es
 pop di
 pop si
 pop bp
 retf
.invalid:
 jmp far repair_abort_far

; FAR stack attr,bottom/right,top/left,count. Preserve the native RET8 ABI.
; Clears stay with their existing owners. Wrapped full-width scrolls move one
; admitted row at a time, bounded by the actual argument rectangle.
terminal_rectangle_far:
 push bp
 mov bp,sp
 sub sp,10
 push bx
 push si
 push di
 push es
 cmp word [screen_cursor_wrap],0
 je .native
 cmp word [bp+12],0
 je .native
 pushf
 pop ax
 and ax,0x600
 cmp ax,0x200
 jne .invalid
 call attribute_repair_plane_admit
 jc .invalid
 cmp byte [bp+10],0
 jne .invalid
 mov al,[screen_last_column]
 cmp al,[bp+8]
 jne .invalid
 xor ax,ax
 mov al,[bp+11]
 mov [bp-6],ax
 xor dx,dx
 mov dl,[bp+9]
 mov [bp-8],dx
 cmp ax,dx
 ja .invalid
 cmp dx,[csi_last_row]
 ja .invalid
 sub dx,ax
 inc dx
 mov ax,[bp+12]
 mov word [bp-2],1
 test ax,0x8000
 jz .magnitude
 mov word [bp-2],0xffff
 neg ax
.magnitude:
 cmp ax,dx
 jbe .count
 mov ax,dx
.count:
 mov [bp-4],ax
 mov ax,[bp+6]
 mov [bp-10],ax
.unit:
 push word [bp-2]
 push word [bp+10]
 push word [bp+8]
 push word [bp-10]
 call far terminal_rectangle_native_far
 mov ax,1
 cmp word [bp-2],1
 je .metadata
 xor ax,ax
.metadata:
 mov dx,[bp-10]
 mov bx,[bp-6]
 mov cx,[bp-8]
 call terminal_region_metadata_move
 call .repair_prefix
 dec word [bp-4]
 jnz .unit
 jmp .done
.native:
 cmp word [bp+12],0
 jne .native_rectangle
 cmp word [screen_attribute_row_bytes],132
 jne .native_rectangle
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call far terminal_wide_clear_far
 jmp .done
.native_rectangle:
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 call far terminal_rectangle_native_far
.done:
 pop es
 pop di
 pop si
 pop bx
 mov sp,bp
 pop bp
 retf 8
.invalid:
 jmp far repair_abort_far

; Only an inherited first field can change when a row boundary moves. A
; retained marker starts its own field. Keep any repair inside this rectangle.
.repair_prefix:
 cmp word [scroll_skip_attribute_scan],0
 jne .repair_done
 mov bx,[bp-6]
 cmp bx,[bp-8]
 je .repair_done
 cmp word [bp-2],1
 je .repair_row
 inc bx
.repair_row:
 mov ax,bx
 mul word [screen_attribute_row_bytes]
 mov di,ax
 mov si,ax
 add si,[screen_attributes_base]
 test byte [si],0x80
 jnz .repair_done
 push bx
 push ax
 call repair_previous_attribute
 pop bx
 mov si,di
 add si,[erase_attribute_values_base]
 cmp al,[si]
 je .repair_done
 ; Original admission has already checked the full owned backing. No
 ; foreground consumer runs during the temporary native scan descriptor.
 push word [screen_cursor_row]
 push word [screen_cursor_column]
 push word [screen_attribute_offset]
 push word [erase_cell_count]
 mov [screen_cursor_row],bx
 mov word [screen_cursor_column],0
 mov [screen_attribute_offset],di
 mov ax,[bp-8]
 inc ax
 mul word [screen_attribute_row_bytes]
 mov [erase_cell_count],ax
 mov ax,2
 push ax
.repair_call:
 call attribute_repair_native
 pop word [erase_cell_count]
 pop word [screen_attribute_offset]
 pop word [screen_cursor_column]
 pop word [screen_cursor_row]
.repair_done:
 ret
terminal_rectangle_end:
scroll_region_repair equ terminal_rectangle_far.repair_call
