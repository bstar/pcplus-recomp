; Parent-owned scalar field display transaction. No child pointers, UART reads,
; DOS calls, parser entry, snapshots or DGROUP buffers. DS=SS, IF enabled.
; Far AX=operation/BX=value, typed result AX; other registers/FLAGS preserved.
;0 begin(packed physical position,FFFF=current native visible cursor)
;1 configure(attribute<<8|width),2 stage(index<<8|nonzero CP437 byte)
;3 present(insert<<8|cursor),4 info(byte index0..10,F000|byte)
; ASPECT_GET_POLICY adds11=status_hidden,12=status_rows, separately versioned.
;5 end(0 adopt cursor+restore shape,1 retire on error without adopting cursor).
; The future versioned RPC must separately authenticate child PSP/DS/lease.
%ifdef ASPECT_GET_DISPLAY
BITS 16
CPU 8086
SEGMENT GET_FIELD_CODE public align=16 class=FARCODE use16
extern terminal_script_field_admit,terminal_script_field_adopt
extern screen_columns,screen_video_row_bytes,text_video_segment
extern text_cga_status_port,text_bios_output,screen_viewport_offset
extern screen_cursor_row,screen_visible_column,attributes_current
extern csi_last_row,screen_attribute_row_bytes
%ifdef ASPECT_GET_POLICY
extern ui_flow_suppressed,ui_flow_coordinate_base
%endif
global terminal_script_field,terminal_script_field_active

terminal_script_field:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 cld
 mov di,bx
 cmp ax,5
 ja .operand
 cmp ax,0
 je .begin
 cmp ax,5
 je .end
 cmp word [cs:terminal_script_field_active],1
 jne .state
 push ax
 call context
 mov bx,ax
 pop ax
 or bx,bx
 jnz .context_error
 cmp ax,1
 je .configure
 cmp ax,2
 je .stage
 cmp ax,3
 je .present
 ; A tagged byte cannot be confused with a typed runtime error0..14.
%ifdef ASPECT_GET_POLICY
 cmp di,12
%else
 cmp di,10
%endif
 ja .operand
 mov bx,di
 mov al,[cs:info+bx]
 mov ah,0xf0
 jmp .done
.context_error:
 mov ax,bx
 jmp .done
.begin:
 cmp word [cs:terminal_script_field_active],0
 jne .state
 call context
 or ax,ax
 jnz .done
 cmp di,0xffff
 jne .position
 mov ax,[screen_cursor_row]
 mov dh,al
 mov ax,[screen_visible_column]
 mov dl,al
 mov di,dx
.position:
 mov ax,di
 cmp al,[cs:geometry_columns]
 jae .operand
 cmp ah,[cs:geometry_rows]
 jae .operand
 mov [cs:info],ax
 xor ax,ax
 mov al,[cs:geometry_columns]
 mov [cs:columns],ax
 mov al,[cs:geometry_limit]
 mov [cs:rows],ax
 mov al,[cs:geometry_rows]
 mov [cs:physical_rows],al
 mov ax,[cs:geometry_video]
 mov [cs:video],ax
 mov al,[cs:geometry_mode]
 mov [cs:mode],al
 mov ax,[screen_viewport_offset]
 mov [cs:origin],ax
 mov [cs:info+7],ax
 mov ax,[attributes_current]
 mov [cs:info+2],al
 xor bh,bh
 mov ah,3
 int 0x10
 mov [cs:shape],cx
 mov [cs:info+3],cx
 mov al,[cs:geometry_columns]
 mov [cs:info+5],al
 mov al,[cs:geometry_limit]
 mov [cs:info+6],al
%ifdef ASPECT_GET_POLICY
 mov ax,[ui_flow_suppressed]
 mov [cs:info+11],al
 mov ax,[ui_flow_coordinate_base]
 mov [cs:info+12],ah
%endif
 mov ax,di
 mov [cs:info+9],ax
 mov al,ah
 xor ah,ah
 mul word [cs:columns]
 mov dx,di
 xor dh,dh
 add ax,dx
 mov [cs:base],ax
 mov word [cs:configured],0
 mov word [cs:presented],0
 mov word [cs:terminal_script_field_active],1
 jmp .ok
.configure:
 mov ax,di
 xor ah,ah
 or ax,ax
 jz .operand
 cmp ax,81
 ja .operand
 mov si,ax
 add si,[cs:base]
 jc .operand
 mov ax,[cs:columns]
 mul word [cs:rows]
 cmp si,ax
 ja .operand
 mov ax,di
 xor ah,ah
 mov [cs:width],ax
 mov ax,di
 mov al,ah
 mov [cs:attribute],al
 mov word [cs:staged],0
 mov word [cs:configured],1
 jmp .ok
.stage:
 cmp word [cs:configured],1
 jne .state
 mov ax,di
 or al,al
 jz .operand
 mov si,ax
 mov al,ah
 xor ah,ah
 cmp ax,[cs:staged]
 jne .operand
 cmp ax,[cs:width]
 jae .operand
 mov bx,ax
 mov ax,si
 mov [cs:cells+bx],al
 inc word [cs:staged]
 jmp .ok
.present:
 cmp word [cs:configured],1
 jne .state
 mov ax,[cs:staged]
 cmp ax,[cs:width]
 jne .state
 mov ax,di
 cmp ah,1
 ja .operand
 xor ah,ah
 cmp ax,[cs:width]
 jae .operand
 mov [cs:cursor],ax
 mov ax,di
 mov [cs:edit],ah
 mov ax,[cs:base]
 mov si,ax
 shl si,1
 xor bp,bp
.cell:
 mov bx,bp
 mov al,[cs:cells+bx]
 mov ah,[cs:attribute]
 mov bx,[text_cga_status_port]
 or bx,[text_bios_output]
 jnz .bios_cell
 mov es,[cs:video]
 mov bx,si
 mov [es:bx],ax
 jmp .next_cell
.bios_cell:
 push ax
 mov ax,si
 shr ax,1
 call coordinate
 xor bh,bh
 mov ah,2
 int 0x10
 pop ax
 mov bl,ah
 xor bh,bh
 mov ah,9
 mov cx,1
 int 0x10
.next_cell:
 add si,2
 inc bp
 cmp bp,[cs:width]
 jb .cell
 mov ax,[cs:base]
 add ax,[cs:cursor]
 call coordinate
 mov [cs:info+9],dx
 xor bh,bh
 mov ah,2
 int 0x10
 mov cx,[cs:shape]
 and ch,0x1f
 cmp byte [cs:edit],0
 je .shape
 mov al,cl
 shr al,1
 inc al
 mov ch,al
.shape:
 mov ah,1
 int 0x10
 mov word [cs:presented],1
 jmp .ok
.end:
 cmp di,1
 ja .operand
 cmp word [cs:terminal_script_field_active],0
 je .ok
 call context
 or ax,ax
 jz .retire_valid
 ; No stale mode/font/cursor writes when a foreign owner or geometry won.
 ; Explicit error retirement drops only this module's private ownership.
 cmp di,1
 jne .done
 mov word [cs:terminal_script_field_active],0
 jmp .done
.retire_valid:
 cmp di,1
 je .error_cursor
 cmp word [cs:presented],0
 je .restore_shape
 mov dx,[cs:info+9]
 mov al,dh
 xor ah,ah
 xor dh,dh
 add dx,[cs:origin]
 call far terminal_script_field_adopt
 or ax,ax
 jnz .done
 jmp .restore_shape
.error_cursor:
 ; Retain current parent logical position after an ordinary field failure.
 ; No adoption of staged field state and no rollback of received text.
 mov ax,[screen_cursor_row]
 mov dh,al
 mov ax,[screen_visible_column]
 mov dl,al
 xor bh,bh
 mov ah,2
 int 0x10
.restore_shape:
 mov cx,[cs:shape]
 mov ah,1
 int 0x10
 mov word [cs:terminal_script_field_active],0
.ok:
 xor ax,ax
 jmp .done
.operand:
 mov ax,7
 jmp .done
.state:
 mov ax,10
.done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf

; Physical linear cell -> BIOS packed coordinate. Bounds checked at configure;
; cross-row fields normalize coordinates instead of issuing invalid BIOS DL.
coordinate:
 xor dx,dx
 div word [cs:columns]
 mov dh,al
 ret

; Revalidate on every scalar operation. No operation writes video or BIOS until
; the complete staged field, active view and current parent owner are admitted.
context:
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 pushf
 pop ax
 test ax,0x200
 jz .state
 call far terminal_script_field_admit
 or ax,ax
 jnz .done
 mov ah,0x0f
 int 0x10
 or bh,bh
 jnz .unsupported
 cmp al,2
 je .color
 cmp al,3
 je .color
 cmp al,7
 jne .unsupported
 mov dx,0xb000
 jmp .video
.color:
 mov dx,0xb800
.video:
 cmp dx,[text_video_segment]
 jne .state
 mov [cs:geometry_video],dx
 mov [cs:geometry_mode],al
 xor al,al
 xchg al,ah
 cmp ax,[screen_columns]
 jne .state
 cmp ax,1
 jb .unsupported
 cmp ax,132
 ja .unsupported
 mov [cs:geometry_columns],al
 shl ax,1
 cmp ax,[screen_video_row_bytes]
 jne .state
 mov ax,0x40
 mov es,ax
 mov al,[es:0x84]
 or al,al
 jnz .row_count
 mov al,24
.row_count:
 inc al
 jz .unsupported
 cmp al,50
 ja .unsupported
 mov [cs:geometry_rows],al
 xor ah,ah
 mov dx,ax
 mov ax,[csi_last_row]
 inc ax
 jz .state
 cmp ax,dx
 ja .state
 mov [cs:geometry_limit],al
%ifdef ASPECT_GET_POLICY
 cmp word [ui_flow_suppressed],1
 ja .state
 mov ax,[ui_flow_coordinate_base]
 test al,al
 jnz .state
 mov al,ah
 xor ah,ah
 or ax,ax
 jz .state
 cmp ax,dx
 ja .state
%endif
 mov ax,[screen_columns]
 add ax,[screen_viewport_offset]
 jc .state
 cmp ax,[screen_attribute_row_bytes]
 ja .state
 cmp word [cs:terminal_script_field_active],0
 je .ok
%ifdef ASPECT_GET_POLICY
 mov ax,[ui_flow_suppressed]
 cmp al,[cs:info+11]
 jne .state
 mov ax,[ui_flow_coordinate_base]
 cmp ah,[cs:info+12]
 jne .state
%endif
 mov al,[cs:geometry_limit]
 xor ah,ah
 cmp ax,[cs:rows]
 jne .state
 mov al,[cs:geometry_rows]
 cmp al,[cs:physical_rows]
 jne .state
 mov al,[cs:geometry_columns]
 cmp ax,[cs:columns]
 jne .state
 mov ax,[cs:geometry_video]
 cmp ax,[cs:video]
 jne .state
 mov al,[cs:geometry_mode]
 cmp al,[cs:mode]
 jne .state
 mov ax,[screen_viewport_offset]
 cmp ax,[cs:origin]
 jne .state
.ok:
 xor ax,ax
 jmp .done
.state:
 mov ax,10
 jmp .done
.unsupported:
 mov ax,3
.done:
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret

terminal_script_field_active: dw 0
configured: dw 0
presented: dw 0
columns: dw 0
rows: dw 0
video: dw 0
origin: dw 0
base: dw 0
shape: dw 0
width: dw 0
staged: dw 0
cursor: dw 0
attribute: db 0
edit: db 0
mode: db 0
geometry_mode: db 0
geometry_columns: db 0
geometry_rows: db 0
geometry_limit: db 0
physical_rows: db 0
geometry_video: dw 0
info: times 11 db 0
%ifdef ASPECT_GET_POLICY
 times 2 db 0
%endif
cells: times 81 db 0
%endif
