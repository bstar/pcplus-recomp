; Resident C public names and declared callbacks for CONFIG_CODE.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define CONFIG_ENTRY NEAR_CDECL_ENTRY
%define CONFIG_REGISTER NEAR_NAMED_SERVICE
%define CONFIG_CDECL NEAR_CDECL_SERVICE
%include "config_abi.inc"
