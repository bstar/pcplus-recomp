; Exact original screen-printer instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINT_SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global print_screen_original
global print_at_e2f9
global print_at_e2fb
global print_at_e2fe
global print_at_e2ff
global print_at_e300
global print_at_e303
global print_at_e306
global print_at_e307
global print_at_e30a
global print_at_e30d
global print_at_e310
global print_at_e311
global print_at_e314
global print_at_e315
global print_at_e318
global print_at_e31b
global print_at_e31e
global print_at_e321
global print_at_e324
global print_at_e327
global print_at_e32a
global print_at_e32d
global print_at_e330
global print_at_e333
global print_at_e335
global print_at_e337
global print_at_e33b
global print_at_e33e
global print_at_e340
global print_at_e344
global print_at_e348
global print_at_e349
global print_at_e34c
global print_at_e34e
global print_at_e351
global print_at_e353
global print_at_e355
global print_at_e356
global print_at_e358
global print_at_e35a
global print_at_e35c
global print_at_e35f
global print_at_e361
global print_at_e363
global print_at_e365
global print_at_e368
global print_at_e36c
global print_at_e370
global print_at_e373
global print_at_e374
global print_at_e377
global print_at_e37a
global print_at_e37b
global print_at_e37f
global print_at_e381
global print_at_e385
global print_at_e388
global print_at_e389
global print_at_e38c
global print_at_e38f
global print_at_e393
global print_at_e396
global print_at_e397
global print_at_e39a
global print_at_e39d
global print_at_e3a1
global print_at_e3a4
global print_at_e3a7
global print_at_e3a8
global print_at_e3ab
global print_at_e3ad
global print_at_e3b1
global print_at_e3b4
global print_at_e3b7
global print_at_e3ba
global print_at_e3bd
global print_at_e3c0
global print_at_e3c3
global print_at_e3c4
global print_at_e3c5
global print_at_e3c7
global print_at_e3c8
extern print_set_cursor
extern printer_device
extern print_status_text
extern printer_status
extern print_status_message
extern print_last_column
extern print_video_offset
extern print_row_limit
extern print_cursor_row
extern print_cursor_column
extern ui_read_byte
extern print_text_mode
extern printer_close
extern printer_open
extern printer_putc
extern printer_flush
extern printer_stream
extern print_region_top
extern print_region_bottom
%else
ORG 0xe2f8
%define print_set_cursor 0x1bbe
%define printer_device 0x1d50
%define print_status_text 0x2b7c
%define printer_status 0x2fb8
%define print_status_message 0x3226
%define print_last_column 0x3258
%define print_video_offset 0x3344
%define print_row_limit 0x334c
%define print_cursor_row 0x399c
%define print_cursor_column 0x399e
%define ui_read_byte 0x6fa0
%define print_text_mode 0x7522
%define printer_close 0x8318
%define printer_open 0x841a
%define printer_putc 0x8436
%define printer_flush 0x8c54
%define printer_stream 0x8ff0
%define print_region_top 0xce0e
%define print_region_bottom 0xce3a
%endif
%include "encodings.inc"
print_screen_original: push bp
print_at_e2f9: mov_load bp,sp
print_at_e2fb: sub sp,0xa
print_at_e2fe: push di
print_at_e2ff: push si
print_at_e300: mov di,[bp+0x4]
print_at_e303: mov ax,print_status_text
print_at_e306: push ax
print_at_e307: call print_status_message
print_at_e30a: add sp,0x2
print_at_e30d: mov ax,print_text_mode
print_at_e310: push ax
print_at_e311: mov ax,printer_device
print_at_e314: push ax
print_at_e315: call printer_open
print_at_e318: add sp,0x4
print_at_e31b: mov [printer_stream],ax
print_at_e31e: mov ax,[print_cursor_row]
print_at_e321: mov [bp-0xa],ax
print_at_e324: mov ax,[print_cursor_column]
print_at_e327: mov [bp-0x8],ax
print_at_e32a: mov dx,[bp-0x2]
print_at_e32d: mov bx,[bp-0x6]
print_at_e330: cmp di,0x1
print_at_e333: jnz short print_at_e33b
print_at_e335: sub_load dx,dx
print_at_e337: mov bx,[print_row_limit]
print_at_e33b: cmp di,0x2
print_at_e33e: jnz short print_at_e349
print_at_e340: mov dx,[print_region_top]
print_at_e344: mov bx,[print_region_bottom]
print_at_e348: inc bx
print_at_e349: cmp di,0x3
print_at_e34c: jnz short print_at_e356
print_at_e34e: mov ax,[print_cursor_row]
print_at_e351: mov_load dx,ax
print_at_e353: mov_load bx,ax
print_at_e355: inc bx
print_at_e356: mov_load di,dx
print_at_e358: cmp_load di,bx
print_at_e35a: jnc short print_at_e3ad
print_at_e35c: mov [bp-0x6],bx
print_at_e35f: sub_load si,si
print_at_e361: mov_load ax,di
print_at_e363: mov_load dx,si
print_at_e365: call print_set_cursor
print_at_e368: push word [printer_stream]
print_at_e36c: push word [print_video_offset]
print_at_e370: call ui_read_byte
print_at_e373: push ax
print_at_e374: call printer_putc
print_at_e377: add sp,0x4
print_at_e37a: inc si
print_at_e37b: cmp [print_last_column],si
print_at_e37f: jnc short print_at_e361
print_at_e381: push word [printer_stream]
print_at_e385: mov ax,0xd
print_at_e388: push ax
print_at_e389: call printer_putc
print_at_e38c: add sp,0x4
print_at_e38f: push word [printer_stream]
print_at_e393: mov ax,0xa
print_at_e396: push ax
print_at_e397: call printer_putc
print_at_e39a: add sp,0x4
print_at_e39d: push word [printer_stream]
print_at_e3a1: call printer_flush
print_at_e3a4: add sp,0x2
print_at_e3a7: inc di
print_at_e3a8: cmp [bp-0x6],di
print_at_e3ab: ja short print_at_e35f
print_at_e3ad: push word [printer_stream]
print_at_e3b1: call printer_close
print_at_e3b4: add sp,0x2
print_at_e3b7: mov ax,[bp-0xa]
print_at_e3ba: mov dx,[bp-0x8]
print_at_e3bd: call print_set_cursor
print_at_e3c0: call printer_status
print_at_e3c3: pop si
print_at_e3c4: pop di
print_at_e3c5: mov_load sp,bp
print_at_e3c7: pop bp
print_at_e3c8: ret
