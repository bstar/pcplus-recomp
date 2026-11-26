; Authenticated scalar screen transaction owner. Caller supplies parent DS=SS;
; outer renderer owns lease identity/authentication and register/FLAGS return.
; All mutable transaction state is CS resident. No parser, UART or child calls.
BITS 16
CPU 8086
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
global terminal_screen_request,terminal_screen_retire
extern terminal_screen_admit,terminal_screen_scope_begin,terminal_screen_scope_end
extern terminal_screen_scroll,terminal_screen_draw_box,terminal_screen_reset_attribute
extern terminal_screen_clear_home,terminal_screen_set_cursor,terminal_screen_read_attribute
extern terminal_screen_write_attribute,terminal_screen_home
extern attributes_normal_value,screen_attribute_row_bytes,ui_window_rows
extern screen_columns,screen_video_row_bytes

; AX32 metadata /33 begin /34 argument /35 commit /36 cancel; BX scalar.
; AX0 success, F000|byte query reply, or typed status. BP/SI/DI preserved.
terminal_screen_request:
 push bp
 push si
 push di
 push ax
 push bx
 call terminal_screen_admit
 pop bx
 pop dx
 or ax,ax
 jnz .refused
 cmp dx,32
 je .metadata
 cmp dx,33
 je .begin
 cmp dx,34
 je .argument
 cmp dx,35
 je .commit
 cmp dx,36
 je .cancel
 jmp .invalid
.metadata:
 mov si,bx
 and bx,0xfeff
 cmp bx,5
 ja .invalid
 shl bx,1
 call [cs:.metadata_getters+bx]
 test si,0x100
 jz .low
 mov al,ah
.low:
 xor ah,ah
 or ax,0xf000
 jmp .done
.metadata_getters:
 dw .normal,.wide,.rows,.last_row,.last_column,.stride
.normal: mov ax,[attributes_normal_value]
 ret
.wide:
 xor ax,ax
 cmp word [screen_attribute_row_bytes],132
 jne .wide_done
 inc ax
.wide_done: ret
.rows: mov ax,[ui_window_rows]
 ret
.last_row: mov ax,[ui_window_rows]
 dec ax
 ret
.last_column: mov ax,[screen_columns]
 dec ax
 ret
.stride: mov ax,[screen_video_row_bytes]
 ret
.begin:
 cmp word [cs:screen_phase],0
 jne .invalid
 cmp bx,7
 ja .invalid
 mov [cs:screen_primitive],bx
 mov word [cs:screen_count],0
 mov word [cs:screen_phase],1
 jmp .success
.argument:
 cmp word [cs:screen_phase],1
 jne .invalid
 mov ax,[cs:screen_count]
 cmp ax,4
 jae .invalid
 mov si,ax
 shl si,1
 mov [cs:screen_arguments+si],bx
 inc word [cs:screen_count]
 jmp .success
.cancel:
 or bx,bx
 jnz .invalid
 call terminal_screen_retire
 jmp .success
.commit:
 or bx,bx
 jnz .invalid
 cmp word [cs:screen_phase],1
 jne .invalid
 mov si,[cs:screen_primitive]
 cmp si,7
 ja .invalid
 mov bx,si
 shl bx,1
 mov ax,[cs:.arity+bx]
 cmp [cs:screen_count],ax
 jne .invalid
 ; Revalidate every value against live admitted physical geometry at commit.
 cmp si,1
 jbe .rectangle
 cmp si,2
 je .attribute
 cmp si,4
 je .cursor
 cmp si,5
 je .offset
 cmp si,6
 je .offset
 jmp .validated
.rectangle:
 mov ax,[cs:screen_arguments]
 cmp ax,255
 ja .invalid
 mov ax,[cs:screen_arguments+2]
 call .packed
 jc .invalid
 mov ax,[cs:screen_arguments+4]
 call .packed
 jc .invalid
 or si,si
 jnz .validated
 mov ax,[cs:screen_arguments+6]
 cmp ax,[ui_window_rows]
 ja .invalid
 jmp .validated
.attribute:
 cmp word [cs:screen_arguments],255
 ja .invalid
 jmp .validated
.cursor:
 mov ax,[cs:screen_arguments]
 cmp ax,[ui_window_rows]
 jae .invalid
 mov ax,[cs:screen_arguments+2]
 cmp word [screen_attribute_row_bytes],132
 jne .physical_column
 cmp ax,131
 ja .invalid
 jmp .validated
.physical_column:
 cmp ax,[screen_columns]
 jae .invalid
 jmp .validated
.offset:
 mov bx,[cs:screen_arguments]
 test bx,1
 jz .invalid
 mov ax,[ui_window_rows]
 mov cx,160
 mul cx
 or dx,dx
 jnz .offset_valid
 cmp bx,ax
 jae .invalid
.offset_valid:
 cmp si,6
 jne .validated
 cmp word [cs:screen_arguments+2],255
 ja .invalid
.validated:
 ; No child can observe/reenter a partially committed transaction.
 call terminal_screen_retire
 cmp si,5
 je .read
 push si
 call terminal_screen_scope_begin
 pop si
 mov bx,si
 shl bx,1
 call [cs:.primitives+bx]
 call terminal_screen_scope_end
.success:
 xor ax,ax
 jmp .done
.read:
 push word [cs:screen_arguments]
 call terminal_screen_read_attribute
 and ax,255
 or ax,0xf000
 jmp .done
.arity: dw 4,3,1,0,2,1,2,0
.primitives: dw .scroll,.box,.reset,.clear,.locate,.read,.write,.home
.scroll:
 push word [cs:screen_arguments+6]
 push word [cs:screen_arguments+4]
 push word [cs:screen_arguments+2]
 push word [cs:screen_arguments]
 call terminal_screen_scroll
 ret
.box:
 push word [cs:screen_arguments+4]
 push word [cs:screen_arguments+2]
 push word [cs:screen_arguments]
 call terminal_screen_draw_box
 ret
.reset:
 mov ax,[cs:screen_arguments]
 call terminal_screen_reset_attribute
 ret
.clear:
 call terminal_screen_clear_home
 ret
.locate:
 mov ax,[cs:screen_arguments]
 mov dx,[cs:screen_arguments+2]
 call terminal_screen_set_cursor
 ret
.write:
 push word [cs:screen_arguments+2]
 push word [cs:screen_arguments]
 call terminal_screen_write_attribute
 ret
.home:
 call terminal_screen_home
 ret
.packed:
 mov dx,ax
 mov al,ah
 xor ah,ah
 cmp ax,[ui_window_rows]
 jae .packed_bad
 mov ax,dx
 xor ah,ah
 cmp ax,[screen_columns]
 jae .packed_bad
 clc
 ret
.packed_bad:
 stc
 ret
.invalid:
 mov ax,7
.refused:
 call terminal_screen_retire
.done:
 pop di
 pop si
 pop bp
 ret

; Retirement is also callable from outer lease/failure paths. AX/FLAGS intact.
terminal_screen_retire:
 mov word [cs:screen_phase],0
 mov word [cs:screen_count],0
 ret
screen_phase: dw 0
screen_primitive: dw 0
screen_count: dw 0
screen_arguments: times 4 dw 0
