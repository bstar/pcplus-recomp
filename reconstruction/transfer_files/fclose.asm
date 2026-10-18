; Exact original receiver/CRT file instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_FILES_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global files_fclose
global files_at_8319
global files_at_831b
global files_at_831e
global files_at_831f
global files_at_8320
global files_at_8323
global files_at_8326
global files_at_832a
global files_at_832c
global files_at_832f
global files_at_8333
global files_at_8335
global files_at_8338
global files_at_8339
global files_at_833c
global files_at_833f
global files_at_8341
global files_at_8343
global files_at_8347
global files_at_834b
global files_at_834e
global files_at_834f
global files_at_8352
global files_at_8355
global files_at_8358
global files_at_835a
global files_at_835b
global files_at_835e
global files_at_8361
global files_at_8363
global files_at_8365
global files_at_8369
global files_at_836b
global files_at_836e
global files_at_836f
global files_at_8372
global files_at_8373
global files_at_8376
global files_at_8379
global files_at_837c
global files_at_837f
global files_at_8383
global files_at_8385
global files_at_8388
global files_at_8389
global files_at_838c
global files_at_838d
global files_at_8390
global files_at_8393
global files_at_8395
global files_at_8396
global files_at_8399
global files_at_839c
global files_at_839d
global files_at_83a0
global files_at_83a3
global files_at_83a6
global files_at_83a9
global files_at_83ac
global files_at_83ad
global files_at_83b0
global files_at_83b3
global files_at_83b5
global files_at_83b7
global files_at_83ba
global files_at_83be
global files_at_83c0
global files_at_83c1
global files_at_83c2
global files_at_83c4
global files_at_83c5
extern files_temp_prefix
extern files_temp_separator
extern files_stream_table
extern files_extra_temporary
extern files_string_copy
extern files_close
extern files_string_append
extern files_fflush
extern files_unsigned_decimal
extern files_unlink
extern files_free_buffer
%else
ORG 0x8318
%define files_temp_prefix 0x7ae4
%define files_temp_separator 0x7ae6
%define files_stream_table 0x7b6a
%define files_extra_temporary 0x7c0e
%define files_string_copy 0x8268
%define files_close 0x868c
%define files_string_append 0x8bea
%define files_fflush 0x8c54
%define files_unsigned_decimal 0x8e6c
%define files_unlink 0x9086
%define files_free_buffer 0xa000
%endif
%include "encodings.inc"
files_fclose: push bp
files_at_8319: mov_load bp,sp
files_at_831b: sub sp,0xe
files_at_831e: push di
files_at_831f: push si
files_at_8320: mov di,0xffff
files_at_8323: mov si,[bp+0x4]
files_at_8326: test byte [si+0x6],0x40
files_at_832a: jz short files_at_832f
files_at_832c: jmp near files_at_83ba
files_at_832f: test byte [si+0x6],0x83
files_at_8333: jnz short files_at_8338
files_at_8335: jmp near files_at_83ba
files_at_8338: push si
files_at_8339: call files_fflush
files_at_833c: add sp,0x2
files_at_833f: mov_load di,ax
files_at_8341: mov_load bx,si
files_at_8343: sub bx,files_stream_table
files_at_8347: mov ax,[bx+files_extra_temporary]
files_at_834b: mov [bp-0x4],ax
files_at_834e: push si
files_at_834f: call files_free_buffer
files_at_8352: add sp,0x2
files_at_8355: mov al,[si+0x7]
files_at_8358: sub_load ah,ah
files_at_835a: push ax
files_at_835b: call files_close
files_at_835e: add sp,0x2
files_at_8361: or_load ax,ax
files_at_8363: jl short files_at_83b7
files_at_8365: cmp word [bp-0x4],0x0
files_at_8369: jz short files_at_83ba
files_at_836b: mov ax,files_temp_prefix
files_at_836e: push ax
files_at_836f: lea ax,[bp-0xe]
files_at_8372: push ax
files_at_8373: call files_string_copy
files_at_8376: add sp,0x4
files_at_8379: lea ax,[bp-0xc]
files_at_837c: mov [bp-0x2],ax
files_at_837f: cmp byte [bp-0xe],0x5c
files_at_8383: jz short files_at_8396
files_at_8385: mov ax,files_temp_separator
files_at_8388: push ax
files_at_8389: lea ax,[bp-0xe]
files_at_838c: push ax
files_at_838d: call files_string_append
files_at_8390: add sp,0x4
files_at_8393: jmp short files_at_8399
files_at_8395: nop
files_at_8396: dec word [bp-0x2]
files_at_8399: mov ax,0xa
files_at_839c: push ax
files_at_839d: push word [bp-0x2]
files_at_83a0: push word [bp-0x4]
files_at_83a3: call files_unsigned_decimal
files_at_83a6: add sp,0x6
files_at_83a9: lea ax,[bp-0xe]
files_at_83ac: push ax
files_at_83ad: call files_unlink
files_at_83b0: add sp,0x2
files_at_83b3: or_load ax,ax
files_at_83b5: jz short files_at_83ba
files_at_83b7: mov di,0xffff
files_at_83ba: mov byte [si+0x6],0x0
files_at_83be: mov_load ax,di
files_at_83c0: pop si
files_at_83c1: pop di
files_at_83c2: mov_load sp,bp
files_at_83c4: pop bp
files_at_83c5: ret
