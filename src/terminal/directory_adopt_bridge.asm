; Selection calls retain DS=SS across existing CONFIG/HOOK ownership banks.
BITS 16
CPU 8086
%ifdef DIRECTORY_RESOURCE_ADOPTION
%include "far_bridge.inc"
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%macro entry 3
 global _%1
 extern _%2
 _%1:
 push bp
 mov bp,sp
 %assign word_index %3-1
 %rep %3
 push word [bp+6+2*word_index]
 %assign word_index word_index-1
 %endrep
 call _%2
 mov sp,bp
 pop bp
 retf
%endmacro
entry directory_adopt_setup,live_setup_select,4
entry directory_adopt_xlt_check,xlt_live_resource_check,4
entry directory_adopt_xlt_publish,xlt_live_resource_adopt,4
entry directory_adopt_script_read,directory_script_read,4
SEGMENT HOOK_CODE public align=16 class=FARCODE use16
global directory_adopt_script_storage
directory_adopt_script_storage: times 80 db 0
extern uart_port_msr
global _directory_adopt_carrier_check
_directory_adopt_carrier_check:
 mov dx,[uart_port_msr]
 in al,dx
 and ax,0x80
 retf
%endif
