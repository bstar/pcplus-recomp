BITS 16
CPU 8086
%include "far_bridge.inc"
SEGMENT MOUSE_CODE public align=16 class=FARCODE use16
%define MOUSE_ENTRY FAR_CDECL_ENTRY
%include "abi.inc"
