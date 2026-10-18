; Resident near ABI for the dedicated controller in PRINT_CODE.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define CONTROLLER_ENTRY NEAR_ENTRY
%define CONTROLLER_SERVICE NEAR_SERVICE
%define CONTROLLER_STACK_SERVICE NEAR_AX_STACK_SERVICE
%include "controller_abi.inc"
