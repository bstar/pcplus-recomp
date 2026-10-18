; Exact original dedicated-printer controller instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINT_CONTROLLER_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global print_controller_original
global print_at_d0d1
global print_at_d0d3
global print_at_d0d7
global print_at_d0d8
global print_at_d0d9
global print_at_d0db
global print_at_d0de
global print_at_d0e1
global print_at_d0e4
global print_at_d0e7
global print_at_d0eb
global print_at_d0ec
global print_at_d0f0
global print_at_d0f4
global print_at_d0f7
global print_at_d0fa
global print_at_d0fb
global print_at_d0fe
global print_at_d101
global print_at_d104
global print_at_d105
global print_at_d108
global print_at_d109
global print_at_d10c
global print_at_d10f
global print_at_d112
global print_at_d115
global print_at_d117
global print_at_d119
global print_at_d11c
global print_at_d11e
global print_at_d121
global print_at_d123
global print_at_d126
global print_at_d128
global print_at_d12b
global print_at_d12f
global print_at_d131
global print_at_d134
global print_at_d137
global print_at_d138
global print_at_d13b
global print_at_d140
global print_at_d142
global print_at_d145
global print_at_d147
global print_at_d149
global print_at_d14b
global print_at_d14e
global print_at_d150
global print_at_d153
global print_at_d155
global print_at_d15a
global print_at_d15c
global print_at_d15f
global print_at_d160
global print_at_d163
global print_at_d166
global print_at_d169
global print_at_d16b
global print_at_d16e
global print_at_d170
global print_at_d173
global print_at_d176
global print_at_d179
global print_at_d17b
global print_at_d17e
global print_at_d180
global print_at_d182
global print_at_d184
global print_at_d187
global print_at_d189
global print_at_d18c
global print_at_d18d
global print_at_d192
global print_at_d194
global print_at_d197
global print_at_d199
global print_at_d19c
global print_at_d19e
global print_at_d1a1
global print_at_d1a3
global print_at_d1a8
global print_at_d1aa
global print_at_d1ad
global print_at_d1af
global print_at_d1b1
global print_at_d1b3
global print_at_d1b5
global print_at_d1b7
global print_at_d1b9
global print_at_d1bb
global print_at_d1bd
global print_at_d1bf
global print_at_d1c1
global print_at_d1c3
global print_at_d1c5
global print_at_d1c7
global print_at_d1ca
global print_at_d1cd
global print_at_d1cf
global print_at_d1d0
global print_at_d1d3
global print_at_d1d6
global print_at_d1d7
global print_at_d1d9
global print_at_d1db
global print_at_d1dd
global print_at_d1e0
global print_at_d1e3
global print_at_d1e6
global print_at_d1e7
global print_at_d1e8
global print_at_d1ed
global print_at_d1ef
global print_at_d1f2
global print_at_d1f4
global print_at_d1f8
global print_at_d1fa
global print_at_d1fc
global print_at_d1fd
global print_at_d1fe
global print_at_d203
global print_at_d205
global print_at_d208
global print_at_d20d
global print_at_d210
global print_at_d215
global print_at_d217
global print_at_d21a
global print_at_d21c
global print_at_d221
global print_at_d223
global print_at_d226
global print_at_d229
global print_at_d22d
global print_at_d22f
global print_at_d231
global print_at_d233
global print_at_d235
global print_at_d237
global print_at_d23a
global print_at_d23c
global print_at_d23d
global print_at_d240
global print_at_d243
global print_at_d246
global print_at_d24a
global print_at_d24d
global print_at_d250
global print_at_d254
global print_at_d255
global print_at_d259
global print_at_d25d
global print_at_d260
global print_at_d264
global print_at_d267
global print_at_d26a
global print_at_d26b
global print_at_d26c
global print_at_d26e
global print_at_d26f
extern controller_break
extern controller_terminal_id
extern printer_device
extern controller_status_text
extern controller_cursor_shape
extern controller_status
extern controller_cursor_flags
extern printer_byte_original
extern controller_next_byte
extern controller_read_key
extern controller_key_available
extern controller_hide_cursor
extern controller_open_mode
extern controller_save
extern controller_restore
extern controller_columns
extern controller_rows
extern printer_close
extern printer_open
extern controller_rx_count
extern controller_dec_family
extern printer_stream
extern controller_other_family
extern controller_dequeue
extern controller_send_key
%else
ORG 0xd0d0
%define controller_break 0x401
%define controller_terminal_id 0x1d18
%define printer_device 0x1d50
%define controller_status_text 0x2b6c
%define controller_cursor_shape 0x2f78
%define controller_status 0x3226
%define controller_cursor_flags 0x333e
%define printer_byte_original 0x36fc
%define controller_next_byte 0x5ca0
%define controller_read_key 0x64fe
%define controller_key_available 0x6530
%define controller_hide_cursor 0x6e5a
%define controller_open_mode 0x7500
%define controller_save 0x765c
%define controller_restore 0x7682
%define controller_columns 0x7a72
%define controller_rows 0x7a82
%define printer_close 0x8318
%define printer_open 0x841a
%define controller_rx_count 0x8e20
%define controller_dec_family 0x8fe8
%define printer_stream 0x8ff0
%define controller_other_family 0x9004
%define controller_dequeue 0xaa65
%define controller_send_key 0xab0b
%endif
%include "encodings.inc"
print_controller_original: push bp
print_at_d0d1: mov_load bp,sp
print_at_d0d3: sub sp,0x130
print_at_d0d7: push di
print_at_d0d8: push si
print_at_d0d9: sub_load ax,ax
print_at_d0db: mov [bp-0x8],ax
print_at_d0de: mov [bp-0x6],ax
print_at_d0e1: mov [bp-0x4],ax
print_at_d0e4: call controller_hide_cursor
print_at_d0e7: lea ax,[bp-0x130]
print_at_d0eb: push ax
print_at_d0ec: push word [controller_rows]
print_at_d0f0: push word [controller_columns]
print_at_d0f4: call controller_save
print_at_d0f7: mov ax,controller_status_text
print_at_d0fa: push ax
print_at_d0fb: call controller_status
print_at_d0fe: add sp,0x2
print_at_d101: mov ax,controller_open_mode
print_at_d104: push ax
print_at_d105: mov ax,printer_device
print_at_d108: push ax
print_at_d109: call printer_open
print_at_d10c: add sp,0x4
print_at_d10f: mov [printer_stream],ax
print_at_d112: call controller_key_available
print_at_d115: or_load ax,ax
print_at_d117: jz short print_at_d13b
print_at_d119: call controller_read_key
print_at_d11c: mov_load di,ax
print_at_d11e: cmp di,0x1b
print_at_d121: jnz short print_at_d12b
print_at_d123: cmp [bp-0x8],di
print_at_d126: jnz short print_at_d12b
print_at_d128: jmp near print_at_d246
print_at_d12b: cmp di,0x3000
print_at_d12f: jnz short print_at_d134
print_at_d131: call controller_break
print_at_d134: mov [bp-0x8],di
print_at_d137: push di
print_at_d138: call controller_send_key
print_at_d13b: cmp word [controller_rx_count],0x0
print_at_d140: jz short print_at_d112
print_at_d142: call controller_dequeue
print_at_d145: mov_load di,ax
print_at_d147: or_load di,di
print_at_d149: jz short print_at_d112
print_at_d14b: cmp di,0x7f
print_at_d14e: jz short print_at_d112
print_at_d150: cmp di,0x14
print_at_d153: jnz short print_at_d166
print_at_d155: cmp word [controller_terminal_id],0x1f
print_at_d15a: jnz short print_at_d15f
print_at_d15c: jmp near print_at_d246
print_at_d15f: push di
print_at_d160: call printer_byte_original
print_at_d163: add sp,0x2
print_at_d166: cmp di,0x1b
print_at_d169: jz short print_at_d16e
print_at_d16b: jmp near print_at_d23c
print_at_d16e: mov_load ax,di
print_at_d170: mov [bp-0x28],al
print_at_d173: mov cx,0x1
print_at_d176: mov [bp-0x2],cx
print_at_d179: mov_load di,cx
print_at_d17b: call controller_next_byte
print_at_d17e: mov_load si,ax
print_at_d180: or_load si,si
print_at_d182: jz short print_at_d17b
print_at_d184: cmp si,0x7f
print_at_d187: jz short print_at_d17b
print_at_d189: mov [bp+di-0x28],al
print_at_d18c: inc di
print_at_d18d: cmp word [controller_dec_family],0x0
print_at_d192: jz short print_at_d1aa
print_at_d194: cmp si,0x2f
print_at_d197: jng short print_at_d1aa
print_at_d199: cmp si,0x3a
print_at_d19c: jnl short print_at_d1aa
print_at_d19e: cmp si,0x34
print_at_d1a1: jnz short print_at_d17b
print_at_d1a3: mov word [bp-0x6],0x1
print_at_d1a8: jmp short print_at_d17b
print_at_d1aa: cmp ax,strict word 0x69
print_at_d1ad: jz short print_at_d21c
print_at_d1af: ja short print_at_d1c1
print_at_d1b1: sub al,0x3b
print_at_d1b3: jz short print_at_d17b
print_at_d1b5: sub al,0x1d
print_at_d1b7: jz short print_at_d1e8
print_at_d1b9: sub al,0x3
print_at_d1bb: jz short print_at_d1fe
print_at_d1bd: sub al,0x6
print_at_d1bf: jz short print_at_d210
print_at_d1c1: sub_load si,si
print_at_d1c3: or_load di,di
print_at_d1c5: jng short print_at_d1db
print_at_d1c7: mov [bp-0x2],di
print_at_d1ca: mov al,[bp+si-0x28]
print_at_d1cd: sub_load ah,ah
print_at_d1cf: push ax
print_at_d1d0: call printer_byte_original
print_at_d1d3: add sp,0x2
print_at_d1d6: inc si
print_at_d1d7: cmp_load si,di
print_at_d1d9: jl short print_at_d1ca
print_at_d1db: sub_load ax,ax
print_at_d1dd: mov [bp-0x4],ax
print_at_d1e0: mov [bp-0x6],ax
print_at_d1e3: jmp near print_at_d112
print_at_d1e6: nop
print_at_d1e7: nop
print_at_d1e8: cmp word [controller_terminal_id],0x1
print_at_d1ed: jnz short print_at_d17b
print_at_d1ef: cmp di,0x1
print_at_d1f2: jng short print_at_d17b
print_at_d1f4: cmp byte [bp+di-0x2a],0x1b
print_at_d1f8: jnz short print_at_d17b
print_at_d1fa: jmp short print_at_d246
print_at_d1fc: nop
print_at_d1fd: nop
print_at_d1fe: cmp word [controller_dec_family],0x0
print_at_d203: jnz short print_at_d208
print_at_d205: jmp near print_at_d17b
print_at_d208: mov word [bp-0x4],0x1
print_at_d20d: jmp near print_at_d17b
print_at_d210: cmp word [controller_other_family],0x0
print_at_d215: jnz short print_at_d21a
print_at_d217: jmp near print_at_d17b
print_at_d21a: jmp short print_at_d1ef
print_at_d21c: cmp word [controller_dec_family],0x0
print_at_d221: jnz short print_at_d226
print_at_d223: jmp near print_at_d17b
print_at_d226: mov bx,[bp-0x4]
print_at_d229: cmp word [bp-0x6],0x0
print_at_d22d: jz short print_at_d233
print_at_d22f: or_load bx,bx
print_at_d231: jnz short print_at_d246
print_at_d233: or_load bx,bx
print_at_d235: jnz short print_at_d23a
print_at_d237: jmp near print_at_d17b
print_at_d23a: jmp short print_at_d1db
print_at_d23c: push di
print_at_d23d: call printer_byte_original
print_at_d240: add sp,0x2
print_at_d243: jmp near print_at_d112
print_at_d246: push word [controller_cursor_flags]
print_at_d24a: call controller_cursor_shape
print_at_d24d: add sp,0x2
print_at_d250: lea ax,[bp-0x130]
print_at_d254: push ax
print_at_d255: push word [controller_rows]
print_at_d259: push word [controller_columns]
print_at_d25d: call controller_restore
print_at_d260: push word [printer_stream]
print_at_d264: call printer_close
print_at_d267: add sp,0x2
print_at_d26a: pop si
print_at_d26b: pop di
print_at_d26c: mov_load sp,bp
print_at_d26e: pop bp
print_at_d26f: ret
