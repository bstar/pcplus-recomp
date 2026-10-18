; Exact original raw monitor instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef MONITOR_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global monitor_resolve_original
global monitor_at_353e
global monitor_at_3540
global monitor_at_3541
global monitor_at_3544
global monitor_at_3545
global monitor_at_3548
global monitor_at_354b
global monitor_at_354c
global monitor_at_354d
global monitor_at_354f
global monitor_at_3551
global monitor_at_3553
global monitor_at_3554
global monitor_at_3557
global monitor_at_3558
global monitor_at_355a
global monitor_at_355e
global monitor_at_3561
global monitor_at_3562
global monitor_at_3564
global monitor_at_3566
global monitor_at_3568
global monitor_at_3569
global monitor_at_356c
global monitor_at_356d
global monitor_at_3570
global monitor_at_3571
global monitor_at_3572
global monitor_at_3575
global monitor_at_3576
global monitor_at_3579
global monitor_at_357a
global monitor_at_357c
global monitor_at_3581
global monitor_at_3583
global monitor_at_3586
global monitor_at_3587
global monitor_at_358a
global monitor_at_358b
global monitor_at_358e
global monitor_at_358f
global monitor_at_3590
global monitor_at_3593
global monitor_at_3596
global monitor_at_3597
global monitor_at_359a
global monitor_at_359b
global monitor_at_359c
global monitor_at_359e
global monitor_at_35a1
global monitor_at_35a2
global monitor_at_35a4
global monitor_at_35a5
extern monitor_environment_name_pointer
extern monitor_probe_mode
extern monitor_separator
extern program_strcpy
extern monitor_close
extern monitor_open
extern program_strcat
extern program_strlen
extern monitor_getenv
extern monitor_path_before
extern monitor_path
%else
ORG 0x353d
%define monitor_environment_name_pointer 0x324c
%define monitor_probe_mode 0x471c
%define monitor_separator 0x471e
%define program_strcpy 0x8268
%define monitor_close 0x8318
%define monitor_open 0x841a
%define program_strcat 0x8bea
%define program_strlen 0x8d18
%define monitor_getenv 0x8e12
%define monitor_path_before 0x8f09
%define monitor_path 0x8f0a
%endif
%include "encodings.inc"
monitor_resolve_original: push bp
monitor_at_353e: mov_load bp,sp
monitor_at_3540: push si
monitor_at_3541: mov ax,monitor_probe_mode
monitor_at_3544: push ax
monitor_at_3545: push word [bp+0x4]
monitor_at_3548: call monitor_open
monitor_at_354b: pop bx
monitor_at_354c: pop bx
monitor_at_354d: mov_load si,ax
monitor_at_354f: or_load si,si
monitor_at_3551: jz short monitor_at_355a
monitor_at_3553: push si
monitor_at_3554: call monitor_close
monitor_at_3557: pop bx
monitor_at_3558: jmp short monitor_at_359e
monitor_at_355a: push word [monitor_environment_name_pointer]
monitor_at_355e: call monitor_getenv
monitor_at_3561: pop bx
monitor_at_3562: mov_load si,ax
monitor_at_3564: or_load si,si
monitor_at_3566: jz short monitor_at_359e
monitor_at_3568: push si
monitor_at_3569: mov ax,monitor_path
monitor_at_356c: push ax
monitor_at_356d: call program_strcpy
monitor_at_3570: pop bx
monitor_at_3571: pop bx
monitor_at_3572: mov ax,monitor_path
monitor_at_3575: push ax
monitor_at_3576: call program_strlen
monitor_at_3579: pop bx
monitor_at_357a: mov_load bx,ax
monitor_at_357c: cmp byte [bx+monitor_path_before],0x5c
monitor_at_3581: jz short monitor_at_3590
monitor_at_3583: mov ax,monitor_separator
monitor_at_3586: push ax
monitor_at_3587: mov ax,monitor_path
monitor_at_358a: push ax
monitor_at_358b: call program_strcat
monitor_at_358e: pop bx
monitor_at_358f: pop bx
monitor_at_3590: push word [bp+0x4]
monitor_at_3593: mov ax,monitor_path
monitor_at_3596: push ax
monitor_at_3597: call program_strcat
monitor_at_359a: pop bx
monitor_at_359b: pop bx
monitor_at_359c: jmp short monitor_at_35a1
monitor_at_359e: mov ax,[bp+0x4]
monitor_at_35a1: pop si
monitor_at_35a2: mov_load sp,bp
monitor_at_35a4: pop bp
monitor_at_35a5: ret
