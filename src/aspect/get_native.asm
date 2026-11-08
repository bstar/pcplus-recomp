; Recovered interactive GET wrappers/shared typed owner/numeric key filter.
; Original6401ccfd, overlay17 F280..F4B6; source-only unwired component.
; DS=SS. Wrappers RET; shared mode owner RET2; filter RET/caller pops2.
; Field service consumes14 bytes; numeric/float/UI/cancel services external.
; Names of sibling modes1/2/3 are intentionally not assigned command names.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_GET_CONTEXT
 %ifdef ASPECT_GET_FLAT
  %error Context bindings are not a flat-byte recovery mode
 %endif
 %define aspect_get_row _runtime_get_row
 %define aspect_get_column _runtime_get_column
 %define aspect_get_attribute _runtime_get_attribute
 %define aspect_get_columns _runtime_get_columns
 %define aspect_get_rows _runtime_get_rows
 %define aspect_get_cursor_origin _runtime_get_origin
 %define aspect_get_status_hidden _runtime_get_status_hidden
 %define aspect_get_scratch _runtime_script_file_mode_pointer
 %define aspect_get_keys_disabled _runtime_when_keyboard_disabled
%endif
%ifdef ASPECT_GET_FLAT
ORG 0xf280
%define aspect_dispatch_read 0x4cb4
%define aspect_get_read_position 0xde27
%define aspect_get_read_attribute 0xdde3
%define aspect_get_read_width 0xde11
%define aspect_get_string_destination 0xdf0b
%define aspect_get_integer_destination 0xde4d
%define aspect_get_long_destination 0xde92
%define aspect_get_float_destination 0xdecb
%define aspect_get_optional 0xe0e4
%define aspect_get_integer_text 0x8e6c
%define aspect_get_long_text 0x9ae8
%define aspect_get_float_text 0xeb38
%define aspect_get_field 0x79d4
%define aspect_get_cursor 0x798e
%define aspect_get_set_cursor 0x1bbe
%define aspect_get_cancel_pending 0x4e6b
%define aspect_get_cancel_dispatch 0x4ebc
%define aspect_get_commit_string 0xe0a4
%define aspect_get_parse_integer 0x984e
%define aspect_get_parse_long 0x9b32
%define aspect_get_parse_float 0xd408
%define aspect_get_copy 0x85b4
%define aspect_get_bell 0x376d
%define aspect_get_destination_kind 0xe38c
%define aspect_get_scratch 0x4b06
%define aspect_get_row 0x399c
%define aspect_get_column 0x399e
%define aspect_get_attribute 0x1f70
%define aspect_get_status_hidden 0x1d46
%define aspect_get_rows 0x7a80
%define aspect_get_columns 0x7a72
%define aspect_get_cursor_origin 0xce2e
%define aspect_get_failure 0xd124
%define aspect_get_keys_disabled 0xe380
%define aspect_get_float_text_pointer 0xe142
%define aspect_get_float_result 0xe150
%define aspect_get_string_filter 0x3f9c
%else
SEGMENT _TEXT public class=CODE use16
global aspect_get,aspect_get_mode1,aspect_get_mode2,aspect_get_mode3
global aspect_get_owner,aspect_get_numeric_filter
extern aspect_dispatch_read
extern aspect_get_read_position
extern aspect_get_read_attribute
extern aspect_get_read_width
extern aspect_get_string_destination
extern aspect_get_integer_destination
extern aspect_get_long_destination
extern aspect_get_float_destination
extern aspect_get_optional
extern aspect_get_integer_text
extern aspect_get_long_text
extern aspect_get_float_text
extern aspect_get_field
extern aspect_get_cursor
extern aspect_get_set_cursor
extern aspect_get_cancel_pending
extern aspect_get_cancel_dispatch
extern aspect_get_commit_string
extern aspect_get_parse_integer
extern aspect_get_parse_long
extern aspect_get_parse_float
extern aspect_get_copy
extern aspect_get_bell
extern aspect_get_destination_kind
extern aspect_get_scratch
extern aspect_get_row
extern aspect_get_column
extern aspect_get_attribute
extern aspect_get_status_hidden
extern aspect_get_rows
extern aspect_get_columns
extern aspect_get_cursor_origin
extern aspect_get_failure
extern aspect_get_keys_disabled
extern aspect_get_float_text_pointer
extern aspect_get_float_result
extern aspect_get_string_filter
%endif
aspect_get:
 sub_load ax,ax
 push ax
 call aspect_get_owner
 ret
aspect_get_mode1:
 mov ax,1
 push ax
 call aspect_get_owner
 ret
aspect_get_mode2:
 mov ax,2
 push ax
 call aspect_get_owner
 ret
aspect_get_mode3:
 mov ax,3
 push ax
 call aspect_get_owner
 ret
aspect_get_owner:
 push bp
 mov_load bp,sp
 sub sp, 0x14
 push di
 mov word [bp-0xe], 0x0
 cmp word [bp + 0x4], 0x2
 jl short L_f2c3
 call aspect_get_read_position
 mov word [bp-0xc], ax
 call aspect_get_read_attribute
 mov word [bp-0x12], ax
 call aspect_get_read_width
 mov word [bp-0x14], ax
L_f2c3:
 call aspect_dispatch_read
 mov [aspect_get_destination_kind], ax
 mov cx, 0xa
 cwd
 idiv cx
 mov word [bp-0xa], dx
 or_load dx,dx
 jnz short L_f2e3
 call aspect_get_string_destination
 mov word [bp-0x2], ax
 mov word [bp-0x10], aspect_get_string_filter
 jmp short L_f311
L_f2e3:
 mov ax, [aspect_get_scratch]
 mov word [bp-0x2], ax
 mov word [bp-0x10], aspect_get_numeric_filter
 mov_load ax,dx
 dec ax
 jz short L_f2fb
 dec ax
 jz short L_f303
 dec ax
 jz short L_f30b
 jmp short L_f311
L_f2fb:
 call aspect_get_integer_destination
 mov word [bp-0x8], ax
 jmp short L_f311
L_f303:
 call aspect_get_long_destination
 mov word [bp-0x6], ax
 jmp short L_f311
L_f30b:
 call aspect_get_float_destination
 mov word [bp-0x4], ax
L_f311:
 cmp word [bp + 0x4], 0x2
 jge short L_f363
 mov al, [aspect_get_column]
 mov ah, byte [aspect_get_row]
 mov word [bp-0xc], ax
 mov ax, [aspect_get_attribute]
 mov word [bp-0x12], ax
 call aspect_get_optional
 or_load ax,ax
 jz short L_f336
 call aspect_get_read_width
 mov_load di,ax
 jmp near L_f3c0
L_f336:
 mov di, 0x50
 cmp word [aspect_get_status_hidden], 0x1
 sbb_load ax,ax
 neg ax
 sub ax, word [aspect_get_rows]
 neg ax
 cmp ax, word [aspect_get_row]
 jg short L_f3c0
 mov ax, [aspect_get_column]
 add_load ax,di
 cmp ax, word [aspect_get_columns]
 jle short L_f3c0
 mov di, word [aspect_get_columns]
 sub di, word [aspect_get_column]
 jmp short L_f3c0
L_f363:
 cmp word [bp + 0x4], 0x2
 jnz short L_f37e
 call aspect_get_optional
 or_load ax,ax
 jz short L_f37e
 mov ax, word [bp-0xa]
 dec ax
 jz short L_f383
 dec ax
 jz short L_f397
 dec ax
 jz short L_f3ae
 jmp short L_f3b4
L_f37e:
 mov di, word [bp-0x14]
 jmp short L_f3c0
L_f383:
 mov ax, 0xa
 push ax
 push word [bp-0x2]
 mov bx, word [bp-0x8]
 push word [bx]
 call aspect_get_integer_text
 add sp, 0x6
 jmp short L_f3b4
L_f397:
 mov ax, 0xa
 push ax
 push word [bp-0x2]
 mov bx, word [bp-0x6]
 push word [bx + 0x2]
 push word [bx]
 call aspect_get_long_text
 add sp, 0x8
 jmp short L_f3b4
L_f3ae:
 push word [bp-0x4]
 call aspect_get_float_text
L_f3b4:
 mov di, word [bp-0x14]
 mov bx, word [bp-0x2]
 mov byte [bx + di], 0x0
 mov word [bp-0xe], bx
L_f3c0:
 or_load di,di
 jz short L_f3fa
 push word [bp-0xc]
 push word [bp-0x12]
 push word [bp-0x2]
 push word [bp-0xe]
 push di
 mov ax, word [bp + 0x4]
 mov cx, 0x2
 cwd
 idiv cx
 push dx
 push word [bp-0x10]
 call aspect_get_field
 mov_load di,ax
 call aspect_get_cursor
 mov word [bp-0xc], ax
 mov al, byte [bp-0xb]
 sub_load ah,ah
 mov dl, byte [bp-0xc]
 sub_load dh,dh
 add dx, word [aspect_get_cursor_origin]
 call aspect_get_set_cursor
L_f3fa:
 cmp di, -0x1
 jnz short L_f404
 mov ax, 0x1
 jmp short L_f406
L_f404:
 sub_load ax,ax
L_f406:
 mov [aspect_get_failure], ax
 or_load ax,ax
 jz short L_f41e
 cmp word [aspect_get_keys_disabled], 0x0
 jnz short L_f41e
 call aspect_get_cancel_pending
 or_load ax,ax
 jz short L_f41e
 call aspect_get_cancel_dispatch
L_f41e:
 mov ax, word [bp-0xa]
 or_load ax,ax
 jz short L_f430
 dec ax
 jz short L_f435
 dec ax
 jz short L_f443
 dec ax
 jz short L_f454
 jmp short L_f472
L_f430:
 call aspect_get_commit_string
 jmp short L_f472
L_f435:
 push word [bp-0x2]
 call aspect_get_parse_integer
 pop bx
 mov bx, word [bp-0x8]
 mov word [bx], ax
 jmp short L_f472
L_f443:
 push word [bp-0x2]
 call aspect_get_parse_long
 pop bx
 mov bx, word [bp-0x6]
 mov word [bx], ax
 mov word [bx + 0x2], dx
 jmp short L_f472
L_f454:
 mov ax, word [bp-0x2]
 mov [aspect_get_float_text_pointer], ax
 mov ax, 0x5
 push ax
 call aspect_get_parse_float
 mov ax, 0x8
 push ax
 mov ax, aspect_get_float_result
 push ax
 push word [bp-0x4]
 call aspect_get_copy
 add sp, 0x6
L_f472:
 pop di
 mov_load sp,bp
 pop bp
 ret 0x2
aspect_get_numeric_filter:
 push bp
 mov_load bp,sp
 mov bx, word [bp + 0x4]
 cmp word [bx], 0xff
 jnc short L_f4b0
 cmp word [bx], 0xd
 jz short L_f4b0
 cmp word [bx], 0x1b
 jz short L_f4b0
 cmp word [bx], 0x8
 jz short L_f4b0
 cmp word [bx], 0x30
 jc short L_f49e
 cmp word [bx], 0x39
 jbe short L_f4b0
L_f49e:
 cmp word [bx], 0x2e
 jz short L_f4b0
 cmp word [bx], 0x2d
 jz short L_f4b0
 call aspect_get_bell
 mov ax, 0xff9d
 jmp short L_f4b2
L_f4b0:
 sub_load ax,ax
L_f4b2:
 mov_load sp,bp
 pop bp
 ret
