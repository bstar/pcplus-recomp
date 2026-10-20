BITS 16
CPU 8086
%include "far_bridge.inc"
SEGMENT MOUSE_CODE public class=FARCODE use16
FAR_CDECL_ENTRY _mouse_test_emit,3
