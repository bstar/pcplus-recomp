; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_row_original
global snapshot_at_3447
global snapshot_at_3449
global snapshot_at_344a
global snapshot_at_344f
global snapshot_at_3451
global snapshot_at_3454
global snapshot_at_3457
global snapshot_at_345a
global snapshot_at_345c
global snapshot_at_3460
global snapshot_at_3464
global snapshot_at_3465
global snapshot_at_3466
global snapshot_at_346a
global snapshot_at_346d
global snapshot_at_346f
global snapshot_at_3471
global snapshot_at_3474
global snapshot_at_3477
global snapshot_at_347a
global snapshot_at_347d
global snapshot_at_3481
global snapshot_at_3482
global snapshot_at_3483
global snapshot_at_3487
global snapshot_at_348a
global snapshot_at_348c
global snapshot_at_348f
global snapshot_at_3491
global snapshot_at_3492
global snapshot_at_3494
global snapshot_at_3495
extern snapshot_video_columns
extern snapshot_shadow_columns
extern snapshot_shadow_offset
extern snapshot_shadow_segment
extern snapshot_copy_original
extern snapshot_video_end
extern snapshot_video_begin
extern snapshot_video_segment
extern snapshot_video_stride
extern snapshot_shadow_enabled
%else
ORG 0x3446
%define snapshot_video_columns 0x3250
%define snapshot_shadow_columns 0x325a
%define snapshot_shadow_offset 0x5dea
%define snapshot_shadow_segment 0x5dec
%define snapshot_copy_original 0x64b8
%define snapshot_video_end 0x77ae
%define snapshot_video_begin 0x77be
%define snapshot_video_segment 0x7a78
%define snapshot_video_stride 0x7a7a
%define snapshot_shadow_enabled 0xcdfa
%endif
%include "encodings.inc"
snapshot_row_original: push bp
snapshot_at_3447: mov_load bp,sp
snapshot_at_3449: push si
snapshot_at_344a: cmp word [snapshot_shadow_enabled],0x0
snapshot_at_344f: jz short snapshot_at_3471
snapshot_at_3451: push word [bp+0x6]
snapshot_at_3454: mov ax,[snapshot_shadow_columns]
snapshot_at_3457: mul word [bp+0x4]
snapshot_at_345a: shl ax,1
snapshot_at_345c: add ax,[snapshot_shadow_offset]
snapshot_at_3460: mov dx,[snapshot_shadow_segment]
snapshot_at_3464: push dx
snapshot_at_3465: push ax
snapshot_at_3466: push word [snapshot_shadow_columns]
snapshot_at_346a: call snapshot_copy_original
snapshot_at_346d: mov_load si,ax
snapshot_at_346f: jmp short snapshot_at_348f
snapshot_at_3471: call snapshot_video_begin
snapshot_at_3474: push word [bp+0x6]
snapshot_at_3477: mov ax,[snapshot_video_stride]
snapshot_at_347a: mul word [bp+0x4]
snapshot_at_347d: mov dx,[snapshot_video_segment]
snapshot_at_3481: push dx
snapshot_at_3482: push ax
snapshot_at_3483: push word [snapshot_video_columns]
snapshot_at_3487: call snapshot_copy_original
snapshot_at_348a: mov_load si,ax
snapshot_at_348c: call snapshot_video_end
snapshot_at_348f: mov_load ax,si
snapshot_at_3491: pop si
snapshot_at_3492: mov_load sp,bp
snapshot_at_3494: pop bp
snapshot_at_3495: ret
