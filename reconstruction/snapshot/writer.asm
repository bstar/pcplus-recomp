; Exact original screen snapshot instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef SNAPSHOT_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global snapshot_write_original
global snapshot_at_3497
global snapshot_at_3499
global snapshot_at_349d
global snapshot_at_349e
global snapshot_at_349f
global snapshot_at_34a2
global snapshot_at_34a3
global snapshot_at_34a6
global snapshot_at_34a7
global snapshot_at_34aa
global snapshot_at_34ab
global snapshot_at_34ac
global snapshot_at_34af
global snapshot_at_34b1
global snapshot_at_34b3
global snapshot_at_34b6
global snapshot_at_34ba
global snapshot_at_34bc
global snapshot_at_34be
global snapshot_at_34bf
global snapshot_at_34c3
global snapshot_at_34c6
global snapshot_at_34c7
global snapshot_at_34c8
global snapshot_at_34ca
global snapshot_at_34cc
global snapshot_at_34cf
global snapshot_at_34d0
global snapshot_at_34d4
global snapshot_at_34d5
global snapshot_at_34d6
global snapshot_at_34d9
global snapshot_at_34da
global snapshot_at_34db
global snapshot_at_34dd
global snapshot_at_34e1
global snapshot_at_34e2
global snapshot_at_34e5
global snapshot_at_34e6
global snapshot_at_34e7
global snapshot_at_34eb
global snapshot_at_34ed
global snapshot_at_34f1
global snapshot_at_34f2
global snapshot_at_34f5
global snapshot_at_34f6
global snapshot_at_34f8
global snapshot_at_34fb
global snapshot_at_3500
global snapshot_at_3502
global snapshot_at_3507
global snapshot_at_350a
global snapshot_at_350e
global snapshot_at_350f
global snapshot_at_3512
global snapshot_at_3513
global snapshot_at_3514
global snapshot_at_3515
global snapshot_at_3519
global snapshot_at_351b
global snapshot_at_351e
global snapshot_at_3521
global snapshot_at_3522
global snapshot_at_3526
global snapshot_at_3528
global snapshot_at_352b
global snapshot_at_352e
global snapshot_at_3530
global snapshot_at_3534
global snapshot_at_3537
global snapshot_at_3538
global snapshot_at_3539
global snapshot_at_353b
global snapshot_at_353c
extern snapshot_filename
extern snapshot_error_text
extern snapshot_refresh
extern snapshot_status
extern snapshot_special_row
extern snapshot_prepare_screen
extern snapshot_row_original
extern snapshot_error
extern snapshot_status_pointer
extern snapshot_append_mode
extern snapshot_newline
extern snapshot_wait_key
extern snapshot_rows
extern program_strcpy
extern snapshot_close
extern snapshot_open
extern program_strlen
extern snapshot_puts
%else
ORG 0x3496
%define snapshot_filename 0x1e5f
%define snapshot_error_text 0x2b3a
%define snapshot_refresh 0x2fb8
%define snapshot_status 0x31bb
%define snapshot_special_row 0x334c
%define snapshot_prepare_screen 0x33f3
%define snapshot_row_original 0x3446
%define snapshot_error 0x427f
%define snapshot_status_pointer 0x42c0
%define snapshot_append_mode 0x4716
%define snapshot_newline 0x4719
%define snapshot_wait_key 0x6bb6
%define snapshot_rows 0x7a74
%define program_strcpy 0x8268
%define snapshot_close 0x8318
%define snapshot_open 0x841a
%define program_strlen 0x8d18
%define snapshot_puts 0x8e88
%endif
%include "encodings.inc"
snapshot_write_original: push bp
snapshot_at_3497: mov_load bp,sp
snapshot_at_3499: sub sp,0x8a
snapshot_at_349d: push di
snapshot_at_349e: push si
snapshot_at_349f: mov ax,snapshot_append_mode
snapshot_at_34a2: push ax
snapshot_at_34a3: mov ax,snapshot_filename
snapshot_at_34a6: push ax
snapshot_at_34a7: call snapshot_open
snapshot_at_34aa: pop bx
snapshot_at_34ab: pop bx
snapshot_at_34ac: mov [bp-0x2],ax
snapshot_at_34af: or_load ax,ax
snapshot_at_34b1: jz short snapshot_at_3530
snapshot_at_34b3: call snapshot_prepare_screen
snapshot_at_34b6: cmp word [bp+0x4],0x0
snapshot_at_34ba: jz short snapshot_at_34c8
snapshot_at_34bc: sub_load ax,ax
snapshot_at_34be: push ax
snapshot_at_34bf: push word [snapshot_status_pointer]
snapshot_at_34c3: call snapshot_status
snapshot_at_34c6: pop bx
snapshot_at_34c7: pop bx
snapshot_at_34c8: sub_load si,si
snapshot_at_34ca: jmp short snapshot_at_3515
snapshot_at_34cc: mov ax,snapshot_newline
snapshot_at_34cf: push ax
snapshot_at_34d0: lea ax,[bp-0x8a]
snapshot_at_34d4: push ax
snapshot_at_34d5: push si
snapshot_at_34d6: call snapshot_row_original
snapshot_at_34d9: pop bx
snapshot_at_34da: pop bx
snapshot_at_34db: mov_load di,ax
snapshot_at_34dd: lea ax,[bp+di-0x8a]
snapshot_at_34e1: push ax
snapshot_at_34e2: call program_strcpy
snapshot_at_34e5: pop bx
snapshot_at_34e6: pop bx
snapshot_at_34e7: cmp [snapshot_special_row],si
snapshot_at_34eb: jnz short snapshot_at_3507
snapshot_at_34ed: lea ax,[bp-0x8a]
snapshot_at_34f1: push ax
snapshot_at_34f2: call program_strlen
snapshot_at_34f5: pop bx
snapshot_at_34f6: mov_load di,ax
snapshot_at_34f8: sub di,0x3
snapshot_at_34fb: cmp byte [bp+di-0x8a],0x1a
snapshot_at_3500: jnz short snapshot_at_3507
snapshot_at_3502: mov byte [bp+di-0x8a],0x20
snapshot_at_3507: push word [bp-0x2]
snapshot_at_350a: lea ax,[bp-0x8a]
snapshot_at_350e: push ax
snapshot_at_350f: call snapshot_puts
snapshot_at_3512: pop bx
snapshot_at_3513: pop bx
snapshot_at_3514: inc si
snapshot_at_3515: cmp [snapshot_rows],si
snapshot_at_3519: jg short snapshot_at_34cc
snapshot_at_351b: push word [bp-0x2]
snapshot_at_351e: call snapshot_close
snapshot_at_3521: pop bx
snapshot_at_3522: cmp word [bp+0x4],0x0
snapshot_at_3526: jz short snapshot_at_3537
snapshot_at_3528: call snapshot_wait_key
snapshot_at_352b: call snapshot_refresh
snapshot_at_352e: jmp short snapshot_at_3537
snapshot_at_3530: lea bx,[snapshot_error_text]
snapshot_at_3534: call snapshot_error
snapshot_at_3537: pop si
snapshot_at_3538: pop di
snapshot_at_3539: mov_load sp,bp
snapshot_at_353b: pop bp
snapshot_at_353c: ret
