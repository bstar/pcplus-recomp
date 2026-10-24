; Recovered PCPlus2.01 telephone-call log controller, overlay4:E2A9..E3AA.
; REA ev_8fbdeb2c8c59e1604bf53207279cda86462bc7e81ef53e858cf6bb35fb013b96.
; Near callee-cleaned stop argument (RET2); DS=SS; BP/DI preserved.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef PHONE_LOG_OMF
SEGMENT _TEXT public class=CODE use16
global phone_log_native
extern phone_log_enabled
extern phone_log_pending
extern phone_log_filename
extern phone_log_append_mode
extern phone_log_error_format
extern phone_log_heading_name
extern phone_log_heading_format
extern phone_log_name
extern phone_log_number
extern phone_log_connect_format
extern phone_log_elapsed
extern phone_log_disconnect_format
extern phone_log_stop_clock
extern phone_log_start_clock
extern phone_log_resolve
extern phone_log_exists
extern phone_log_prepare
extern phone_log_open
extern phone_log_sprintf
extern phone_log_notice
extern phone_log_fprintf
extern phone_log_time
extern phone_log_date
extern phone_log_close
%define short
%else
ORG 0xe2a9
%define phone_log_enabled 0x1d6a
%define phone_log_pending 0x333a
%define phone_log_filename 0x3320
%define phone_log_append_mode 0x7094
%define phone_log_error_format 0x4a08
%define phone_log_heading_name 0x4a1a
%define phone_log_heading_format 0x4a20
%define phone_log_name 0xe650
%define phone_log_number 0xe669
%define phone_log_connect_format 0x7097
%define phone_log_elapsed 0x2c7c
%define phone_log_disconnect_format 0x70ad
%define phone_log_stop_clock 0x37a5
%define phone_log_start_clock 0x3f61
%define phone_log_resolve 0x353d
%define phone_log_exists 0x3673
%define phone_log_prepare 0x48a1
%define phone_log_open 0x841a
%define phone_log_sprintf 0x82b6
%define phone_log_notice 0x427f
%define phone_log_fprintf 0x9786
%define phone_log_time 0x498b
%define phone_log_date 0x36d4
%define phone_log_close 0x8318
%endif
phone_log_native:
L_e2a9: push bp
L_e2aa: mov_load bp,sp
L_e2ac: sub sp,0x56
L_e2af: push di
L_e2b0: mov di,[bp+0x4]
L_e2b3: or_load di,di
L_e2b5: jz short L_e2bc
L_e2b7: call phone_log_stop_clock
L_e2ba: jmp short L_e2bf
L_e2bc: call phone_log_start_clock
L_e2bf: cmp word [phone_log_enabled],0x0
L_e2c4: jnz short L_e2cf
L_e2c6: mov word [phone_log_pending],0x0
L_e2cc: jmp near L_e3a4
L_e2cf: mov ax,phone_log_filename
L_e2d2: push ax
L_e2d3: call phone_log_resolve
L_e2d6: pop bx
L_e2d7: push ax
L_e2d8: call phone_log_exists
L_e2db: pop bx
L_e2dc: cmp ax,strict word 0x1
L_e2df: sbb_load ax,ax
L_e2e1: neg ax
L_e2e3: mov [bp-0x4],ax
L_e2e6: or_load di,di
L_e2e8: jz short L_e2fb
L_e2ea: cmp word [phone_log_pending],0x0
L_e2ef: jnz short L_e2f4
L_e2f1: jmp near L_e3a4
L_e2f4: or_load ax,ax
L_e2f6: jz short L_e2fb
L_e2f8: jmp near L_e3a4
L_e2fb: mov ax,phone_log_filename
L_e2fe: push ax
L_e2ff: call phone_log_resolve
L_e302: pop bx
L_e303: push ax
L_e304: call phone_log_prepare
L_e307: pop bx
L_e308: mov ax,phone_log_append_mode
L_e30b: push ax
L_e30c: mov ax,phone_log_filename
L_e30f: push ax
L_e310: call phone_log_resolve
L_e313: pop bx
L_e314: push ax
L_e315: call phone_log_open
L_e318: pop bx
L_e319: pop bx
L_e31a: mov [bp-0x2],ax
L_e31d: or_load ax,ax
L_e31f: jnz short L_e33b
L_e321: mov ax,phone_log_filename
L_e324: push ax
L_e325: mov ax,phone_log_error_format
L_e328: push ax
L_e329: lea ax,[bp-0x56]
L_e32c: push ax
L_e32d: call phone_log_sprintf
L_e330: add sp,0x6
L_e333: lea bx,[bp-0x56]
L_e336: call phone_log_notice
L_e339: jmp short L_e3a4
L_e33b: or_load di,di
L_e33d: jnz short L_e379
L_e33f: cmp [bp-0x4],di
L_e342: jz short L_e355
L_e344: mov ax,phone_log_heading_name
L_e347: push ax
L_e348: mov ax,phone_log_heading_format
L_e34b: push ax
L_e34c: push word [bp-0x2]
L_e34f: call phone_log_fprintf
L_e352: add sp,0x6
L_e355: mov ax,0x1
L_e358: push ax
L_e359: call phone_log_time
L_e35c: pop bx
L_e35d: push ax
L_e35e: call phone_log_date
L_e361: push ax
L_e362: mov ax,phone_log_number
L_e365: push ax
L_e366: mov ax,phone_log_name
L_e369: push ax
L_e36a: mov ax,phone_log_connect_format
L_e36d: push ax
L_e36e: push word [bp-0x2]
L_e371: call phone_log_fprintf
L_e374: add sp,0xc
L_e377: jmp short L_e393
L_e379: mov ax,phone_log_elapsed
L_e37c: push ax
L_e37d: mov ax,0x1
L_e380: push ax
L_e381: call phone_log_time
L_e384: pop bx
L_e385: push ax
L_e386: mov ax,phone_log_disconnect_format
L_e389: push ax
L_e38a: push word [bp-0x2]
L_e38d: call phone_log_fprintf
L_e390: add sp,0x8
L_e393: cmp di,0x1
L_e396: sbb_load ax,ax
L_e398: neg ax
L_e39a: mov [phone_log_pending],ax
L_e39d: push word [bp-0x2]
L_e3a0: call phone_log_close
L_e3a3: pop bx
L_e3a4: pop di
L_e3a5: mov_load sp,bp
L_e3a7: pop bp
L_e3a8: ret word 0x2
