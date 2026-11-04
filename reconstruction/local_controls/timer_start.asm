; Original call-clock start CS:3F61..3F72 (18 bytes), independent of log IO.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0x3f61
%define elapsed_start_stamp 0xcff2
%define elapsed_gettime 0x778c
%define elapsed_seconds 0x3f73
%define elapsed_start_seconds 0xcd8e
%else
SEGMENT ELAPSED_TIMER_CODE public align=16 class=FARCODE use16
extern elapsed_start_stamp,elapsed_gettime,elapsed_start_seconds
extern elapsed_seconds
global elapsed_start
%endif
elapsed_start:
 mov ax,elapsed_start_stamp
 push ax
 call elapsed_gettime
 call elapsed_seconds
 mov [elapsed_start_seconds],ax
 mov [elapsed_start_seconds+2],dx
 ret
