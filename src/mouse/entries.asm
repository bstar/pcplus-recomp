BITS 16
CPU 8086
%include "far_bridge.inc"
SEGMENT _TEXT public class=CODE use16
%define MOUSE_ENTRY NEAR_CDECL_ENTRY
%include "abi.inc"
NEAR_NAMED_SERVICE mouse_keyboard_poll,keyboard_poll
NEAR_NAMED_SERVICE mouse_keyboard_read,keyboard_read
