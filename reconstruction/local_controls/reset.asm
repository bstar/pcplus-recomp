; Original local Reset Terminal entry CS:1368, excluding the following NOP.
; DS=SS. The caller owns the cdecl argument cleanup; native reset owns behavior.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0x1368
%define ansi_escape_service_20a4 0x20a4
%else
SEGMENT _TEXT public class=CODE use16
extern ansi_escape_service_20a4
global local_reset_1368
%endif
local_reset_1368:
 mov ax,1
 push ax
 call ansi_escape_service_20a4
 add sp,2
 ret
