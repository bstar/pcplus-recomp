; New CONFIG parent service. Resource resolver already lives in
; CONFIG_CODE; the adapter adds no resident _TEXT or DGROUP bytes.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
%include "far_bridge.inc"
NEAR_CDECL_SERVICE _meta_bank_resource,_resource_pcplus_path,3
