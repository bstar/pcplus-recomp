; Optional staged RIS row-default owner. No live geometry/video/serial writes.
; Far register ABI AX=requested effective rows1..50; AX=0 success,2 not captured,
; 3 invalid baseline/request. Preserve all other registers and entry flags.
; Caller owns the larger geometry transaction and must serialize foreground use.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
extern reset_ready,reset_word_addresses,reset_word_addresses_end,reset_words
extern csi_row_count,csi_last_row,erase_cell_count,screen_attribute_row_bytes
extern screen_columns,screen_video_row_bytes,screen_last_column
extern screen_first_row,screen_last_row,csi_origin_row,csi_origin_bottom
extern screen_cursor_row,screen_cursor_column,screen_visible_column
extern screen_previous_row,screen_previous_column,csi_saved_row,screen_video_offset,screen_attribute_offset
global terminal_reset_resize_rows_far

; Read one captured default: AX=root address -> DX=value,BX=default cell,CF0.
; Unknown table addresses fail without a write; preserve SI/CX/DI/BP/ES.
get_default:
 push si
 mov si,reset_word_addresses
 mov bx,reset_words
.find:
 cmp si,reset_word_addresses_end
 jae .missing
 cmp ax,[si]
 je .found
 add si,2
 add bx,2
 jmp .find
.found:
 mov dx,[bx]
 clc
 pop si
 ret
.missing:
 stc
 pop si
 ret

; DI=staging cursor. Table cells, not external/live pointers, are retained.
stage_default:
 call get_default_pointer
 jc .done
 mov [di],bx
 mov [di+2],dx
 add di,4
 inc word [bp-16]
.done:
 ret
get_default_pointer:
 push dx
 call get_default
 pop dx
 ret

%macro read_default 1
 mov ax,%1
 call get_default
 jc .invalid
%endmacro
%macro stage 1
 mov ax,%1
 call stage_default
 jc .invalid
%endmacro

terminal_reset_resize_rows_far:
 pushf
 push bp
 mov bp,sp
 sub sp,80
 push bx
 push cx
 push dx
 push si
 push di
 push es
 mov [bp-2],ax
 mov ax,ds
 mov bx,ss
 cmp ax,bx
 jne .invalid
 cmp word [reset_ready],1
 jne .uncaptured
 cmp word [bp-2],1
 jb .invalid
 cmp word [bp-2],50
 ja .invalid
 read_default csi_row_count
 cmp dx,1
 jb .invalid
 cmp dx,50
 ja .invalid
 dec dx
 mov [bp-4],dx ;Old maximum, independently of the current peer state.
 read_default csi_last_row
 cmp dx,[bp-4]
 jne .invalid
 read_default screen_columns
 cmp dx,80
 jne .invalid
 read_default screen_video_row_bytes
 cmp dx,160
 jne .invalid
 read_default screen_attribute_row_bytes
 cmp dx,80
 je .stride
 cmp dx,132
 jne .invalid
.stride:
 mov [bp-6],dx
 read_default screen_last_column
 inc dx
 cmp dx,[bp-6]
 jne .invalid
 mov ax,[bp-4]
 inc ax
 mul word [bp-6]
 or dx,dx
 jnz .invalid
 cmp ax,4096
 ja .invalid
 mov cx,ax
 read_default erase_cell_count
 cmp dx,cx
 jne .invalid
 mov ax,[bp-2]
 mul word [bp-6]
 or dx,dx
 jnz .invalid
 cmp ax,4096 ;Both near byte planes and8192-byte far shadow must fit.
 ja .invalid
 mov [bp-24],ax
 read_default screen_cursor_column
 cmp dx,[bp-6]
 jae .invalid
 mov [bp-8],dx
 read_default screen_visible_column
 cmp dx,80
 jae .invalid
 mov [bp-10],dx
 read_default screen_cursor_row
 cmp dx,[bp-4]
 ja .invalid
 mov [bp-12],dx
 read_default screen_previous_row
 cmp dx,[bp-12]
 jne .invalid
 read_default screen_previous_column
 cmp dx,[bp-8]
 jne .invalid
 mov dx,[bp-12]
 mov ax,160
 mul dx
 mov cx,[bp-10]
 shl cx,1
 add cx,ax
 read_default screen_video_offset
 cmp dx,cx
 jne .invalid
 mov ax,[bp-12]
 mul word [bp-6]
 add ax,[bp-8]
 mov cx,ax
 read_default screen_attribute_offset
 cmp dx,cx
 jne .invalid
 ; Stage every result before committing any captured word.
 mov word [bp-16],0
 lea di,[bp-80]
 mov dx,[bp-2]
 stage csi_row_count
 mov dx,[bp-2]
 dec dx
 stage csi_last_row
 mov dx,[bp-24]
 stage erase_cell_count
 mov si,row_fields
.row:
 mov ax,[cs:si]
 or ax,ax
 jz .offsets
 call get_default
 jc .invalid
 cmp dx,[bp-4]
 ja .invalid
 mov cx,[bp-2]
 dec cx
 cmp word [cs:si+2],0
 je .clamp
 cmp dx,[bp-4]
 je .follow
.clamp:
 cmp dx,cx
 jbe .keep
.follow:
 mov dx,cx
.keep:
 cmp ax,screen_cursor_row
 jne .not_cursor
 mov [bp-14],dx
.not_cursor:
 ; Keep old margin endpoints for pair validation. Clamping invalid old pairs
 ; must not accidentally turn corrupt defaults into apparently valid output.
 cmp ax,screen_first_row
 jne .last
 mov cx,[bx]
 mov [bp-18],cx
.last:
 cmp ax,screen_last_row
 jne .origin
 mov cx,[bx]
 cmp cx,[bp-18]
 jb .invalid
.origin:
 cmp ax,csi_origin_row
 jne .bottom
 mov cx,[bx]
 mov [bp-20],cx
.bottom:
 cmp ax,csi_origin_bottom
 jne .staged
 mov cx,[bx]
 cmp cx,[bp-20]
 jb .invalid
.staged:
 ; BX already identifies this captured default, DX its staged value.
 mov [di],bx
 mov [di+2],dx
 add di,4
 inc word [bp-16]
 add si,4
 jmp .row
.offsets:
 mov ax,[bp-14]
 mov cx,160
 mul cx
 mov dx,[bp-10]
 shl dx,1
 add dx,ax
 stage screen_video_offset
 mov ax,[bp-14]
 mul word [bp-6]
 add ax,[bp-8]
 mov dx,ax
 stage screen_attribute_offset
 mov cx,[bp-16]
 lea si,[bp-80]
.commit:
 mov bx,[si]
 mov dx,[si+2]
 mov [bx],dx
 add si,4
 loop .commit
 xor ax,ax
 jmp .done
.uncaptured:
 mov ax,2
 jmp .done
.invalid:
 mov ax,3
.done:
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 mov sp,bp
 pop bp
 popf
 retf

; Follow old maximum only for bottom endpoints; other row defaults clamp.
row_fields:
 dw screen_first_row,0,screen_last_row,1,csi_origin_row,0,csi_origin_bottom,1
 dw screen_cursor_row,0,screen_previous_row,0,csi_saved_row,0,0
