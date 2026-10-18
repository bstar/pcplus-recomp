; Resident public entries and declared resident callbacks for MODEM_CODE.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
%include "far_bridge.inc"
%define MODEM_ENTRY NEAR_ENTRY
%define MODEM_SERVICE NEAR_NAMED_SERVICE
%define MODEM_CDECL_SERVICE NEAR_CDECL_SERVICE
%include "modem_abi.inc"
